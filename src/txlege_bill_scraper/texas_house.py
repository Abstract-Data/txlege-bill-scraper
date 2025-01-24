import pandas as pd
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Final, Dict, Any, Optional, Self
import tomli
from pathlib import Path
from pydantic import Field as PydanticField, HttpUrl, BaseModel, ConfigDict
from pydantic.dataclasses import dataclass as pydantic_dataclass
from enum import StrEnum
from functools import partial
import re

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import undetected_chromedriver as uc

DOWNLOAD_PATH = Path.home() / 'Downloads'
BRAVE_PATH = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'

options = uc.ChromeOptions()
options.binary_location = str(BRAVE_PATH)
options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
# options.add_argument("start-maximized")  # ensure window is full-screen
options.page_load_strategy = "none"  # Load the page as soon as possible

driver = uc.Chrome(options=options)


with open(Path(__file__).parent / "tlo_urls.toml", "rb") as config:
    urls: Dict = tomli.load(config)

TLO_MAIN_URL = urls.get("MAIN-TLO-URL")
TLO_MEMBER_BILL_LIST_URL = TLO_MAIN_URL + urls["MEMBER-URLS"]["BILL-LIST"]
TLO_CHAMBER_LIST = TLO_MAIN_URL + urls["CHAMBER-URLS"]["MEMBER-LIST"]
TLO_BILL_TEXT = TLO_MAIN_URL + urls.get("BILL-TEXT-BASE")

LEGISLATIVE_SESSION: str = "87R"
BILL_TYPE: str = "HB" or "SB"
BILL_NUMBER: int = 1

MEMBER_BILL_TYPE_URL = "https://capitol.texas.gov/reports/report.aspx?LegSess={session}}&ID={bill_writer_type}&Code={member_id}"
def get_link(value: str, _driver: uc.Chrome, by: By = By.LINK_TEXT) -> str:
    return _driver.find_element(by, value).get_attribute('href')

class Chamber(StrEnum):
    HOUSE = "H"
    SENATE = "S"

class MemberPage(StrEnum):
    HOUSE = "https://www.house.texas.gov/members/{member_id}"


class BillAssociation(StrEnum):
    AUTHOR = "Author"
    COAUTHOR = "Coauthor"
    SPONSOR = "Sponsor"
    COSPONSOR = "Cosponsor"
    AMENDMENT = "Amendment"

BILL_DICT = {}

class LegislatorBase(BaseModel):
    id: str
    member_url: str
    prefix: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    district: Optional[str] = None
    capitol_office: Optional[str] = None
    capitol_phone: Optional[str] = None
    urls: Dict[str, str] = field(default_factory=dict)
    # bills_authored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_sponsored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_coauthored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_cosponsored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # amendments_authored: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def fetch_member_details(self, _driver: uc.Chrome):
        _driver.get(self.member_url)
        _wait = WebDriverWait(_driver, 10)
        _get_link = partial(get_link, _driver=_driver)
        _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Bills Authored")))
        member_name = (
            _driver
            .find_element(By.ID, "usrHeader_lblPageTitle")
            .text
            .replace("Information For", "")
            .strip()
        )
        if 'Rep' in member_name:
            self.prefix = 'REPRESENTATIVE'
            self.district = "HD "
            member_name = member_name.replace("Rep. ", "")
        elif 'Sen' in member_name:
            self.prefix = 'SENATOR'
            self.prefix = "SD "
            member_name = member_name.replace("Sen. ", "")

        member_contact = _driver.find_element(By.ID, "contactInfo")
        self.district += member_contact.find_element(By.ID, "lblDistrict").text
        _split_member_name = member_name.split()
        if len(_split_member_name) == 2:
            self.last_name = _split_member_name[1]
            self.first_name = _split_member_name[0]
        if len(_split_member_name) == 3:
            if len(_split_member_name[1]) == 1:
                self.first_name = f"{_split_member_name[0]} {_split_member_name[1]}"
                self.last_name = _split_member_name[2]
            else:
                self.first_name = _split_member_name[0]
                self.last_name = f"{_split_member_name[1]} {_split_member_name[2]}"
        self.capitol_office = member_contact.find_element(By.ID, "lblCapitolOffice").text
        self.capitol_phone = member_contact.find_element(By.ID, "lblCapitolPhone").text
        self.urls = {
            'authored': _get_link("Bills Authored"),
            'sponsored': _get_link("Bills Sponsored"),
            'co-authored': _get_link("Bills Coauthored"),
            'co-sponsored': _get_link("Bills Cosponsored"),
            'amendments': _get_link("Amendments Authored")
        }
        return self

    def fetch_legislation_details(self, _driver: uc.Chrome):
        for url in self.urls['authored']:
            _bill_details = BillDetail(
                bill_number=url.split('=')[-1],
                bill_url=url
            )
            if _bill_details.bill_number not in BILL_DICT.keys():
                _bill_details.fetch_bill_details(_driver)
                BILL_DICT[_bill_details.bill_number] = _bill_details


class BillStage(BaseModel):
    version: str
    pdf: str
    txt: str
    word_doc: str
    fiscal_note: Optional[str] = None
    analysis: Optional[str] = None
    witness_list: Optional[str] = None
    summary_of_action: Optional[str] = None


class BillDetail(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    bill_url: str
    bill_number: Optional[str] = None
    status: Optional[str] = None
    caption: Optional[str] = None
    last_action_dt: Optional[str] = None
    action_list: Optional[pd.DataFrame] = None

    def fetch_bill_details(self, _driver: uc.Chrome):
        # self.bill_number = self.bill_url.split('=')[-1]
        _driver.get(self.bill_url)
        _wait = WebDriverWait(_driver, 10)
        _wait.until(EC.element_to_be_clickable((By.ID, "Form1")))
        _bill_detail_table = _driver.find_element(By.ID, "Form1").text.split('\n')

        _last_action = next(
            (_bill_detail_table
            .pop(i)
            .replace(_c, "")
            for i, x in enumerate(_bill_detail_table)
            if (_c := "Last Action: ")
               in x),
            None
        )

        _caption_version = next(
            (_bill_detail_table
             .pop(i)
             .replace(_c, "")
             for i, x in enumerate(_bill_detail_table)
             if (_c := "Caption Version: ")
             in x),
            None
        )

        _caption_text = next(
            (_bill_detail_table
             .pop(i)
             .replace(_c, "")
             for i, x in enumerate(_bill_detail_table)
             if (_c := "Caption Text: ")
             in x),
            None
        )
        self.status = _caption_version
        self.caption = _caption_text
        self.last_action_dt = re.compile(r'\d{2}/\d{2}/\d{4}').match(_last_action).group() if _last_action else None

        #TODO: Fix this to avoid the StopIteration error.
        find_where_actions_start = (
            i + 2
            for i, x in enumerate(_bill_detail_table)
            if x.startswith("Actions:"))
        if not find_where_actions_start:
            return self

        t_header = ['Description', 'Comment', 'Date', 'Time', 'Journal Page']
        action_list = []
        for x in _bill_detail_table[find_where_actions_start:]:
            t_row= x.split()
            t_dict = dict(zip(t_row, t_header))
            action_list.append(t_dict)
        self.action_list = pd.DataFrame(action_list)

        _driver.find_element(By.LINK_TEXT, "Text").click()
        _bill_version_table = driver.find_element(By.ID, "Form1")
        _header = _bill_version_table.find_elements(By.TAG_NAME, "tr")[0]
        _header_text = [x.text.replace('\n', ' ') for x in _header.find_elements(By.TAG_NAME, "td")]
        bill_stages = []
        for x in _bill_version_table.find_elements(By.TAG_NAME, "tr")[1:]:
            cells = x.find_elements(By.TAG_NAME, "td")
            bill_stage = BillStage(
                version=cells[0].text,
                pdf=cells[1].find_element(By.LINK_TEXT, "PDF").get_attribute("href"),
                txt=cells[1].find_element(By.LINK_TEXT, "Text").get_attribute("href"),
                word_doc=cells[1].find_element(By.LINK_TEXT, "Word").get_attribute("href"),
                fiscal_note=cells[2].text if len(cells) > 2 else None,
                analysis=cells[3].text if len(cells) > 3 else None,
                witness_list=cells[4].text if len(cells) > 4 else None,
                summary_of_action=cells[5].text if len(cells) > 5 else None
            )
            bill_stages.append(bill_stage)
        return self

@pydantic_dataclass
class TxLegeLoader:
    chamber: Chamber
    lege_session: str = PydanticField(default=LEGISLATIVE_SESSION)
    url: HttpUrl = PydanticField(default=TLO_CHAMBER_LIST)
    page: Any = PydanticField(init=False)
    members: list = PydanticField(init=False)

    def __repr__(self):
        return f"Texas {self.chamber} Members for {self.lege_session.upper()} Legislative Session"


    def get_legislators(self, _driver: uc.Chrome) -> Self:
        _driver.get("https://capitol.texas.gov/Home.aspx")
        wait = WebDriverWait(_driver, 10)
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House"))).click()
        wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House Members"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "content"))).click()
        member_list = driver.find_element(By.ID, "content")
        links = member_list.find_elements(By.TAG_NAME, "a")
        member_links = iter(x.get_attribute("href") for x in links)
        _member_gen = [LegislatorBase(id=x.split('=')[-1], member_url=x) for x in member_links]
        self.members = [x.fetch_member_details(_driver).fetch_legislation_details(_driver) for x in _member_gen]
        return self


@pydantic_dataclass
class LegislativeMember:
    prefix: str
    last_name: str
    tlo_id: str
    legislation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    page_text: Any = field(init=False)
    member_url: HttpUrl = None

    def __repr__(self):
        return f"TLO Desc for: {self.prefix} {self.last_name}"

    def __post_init__(self):
        _session_num = next(iter(self.legislation))
        self.__bill_url = TLO_MEMBER_BILL_LIST_URL.format(
            _session_num, self.tlo_id
        )
        self.legislation[_session_num] = self.fetch_legislation(self.__bill_url)

    def fetch_legislation(self, __url=None) -> Dict[str, Dict[str, Any]]:
        _page = requests.get(__url)
        self.page_text = _page.text
        self.member_url = HttpUrl(_page.url)
        _soup = BeautifulSoup(_page.content, "html.parser")
        _tables = _soup.find_all("table")
        bills = {}
        for table in _tables:
            bill_details = {}
            _sections = [x for x in table.find_all("tr")]
            _bill_no = _sections[0].find_all("td")[0].text
            if len(_sections) >= 3:
                bill_details.update(
                    {
                        _sections[0]
                        .find_all("td")[1]
                        .text.replace(":", ""): [
                            x.strip()
                            for x in _sections[0].find_all("td")[2].text.split("|")
                        ]
                    }
                )
                bill_details.update(
                    {
                        _sections[1]
                        .find_all("td")[1]
                        .text.replace(":", ""): [
                            x.strip()
                            for x in _sections[1].find_all("td")[2].text.split("|")
                        ]
                    }
                )
                bill_details.update(
                    {
                        _sections[2]
                        .find_all("td")[1]
                        .text.replace(":", "")
                        .strip(): _sections[2]
                        .find_all("td")[2]
                        .text
                    }
                )
                if len(_sections) == 4:
                    bill_details.update(
                        {
                            _sections[3]
                            .find_all("td")[1]
                            .text.replace(":", ""): _sections[3]
                            .find_all("td")[2]
                            .text
                        }
                    )
            bills.update({_bill_no: bill_details})
        return bills

    def fiscal_notes(self):
        # TODO: Build reader to pull fiscal notes from TLO for each bill number.
        if self.legislation:
            fiscal_notes = {}
            for bill, details in self.legislation.items():
                if details.get("Fiscal Note"):
                    fiscal_notes.update({bill: details.get("Fiscal Note")})
            return fiscal_notes

    def get_bill(self, chamber, number):
        return self.legislation.get(f"{chamber.upper()} {number}")


# @dataclass
# class BillDetails:
#     chamber: str
#     number: int
#     _session: str = LEGISLATIVE_SESSION
#
#     def __post_init__(self):
#         self.last_action = None
#         self.caption_version = None
#         self.caption_text = None
#         self.authors = None
#         self.coauthors = None
#         self.sponsors = None
#         self.subjects = None
#         self.companion = None
#         self.house_committee = None
#         self.house_committee_details = {self.house_committee: None}
#         self.house_committee_details['status'] = None
#         self.house_committee_details['votes'] = None
#         self.senate_committee = None
#         self.senate_committee_details = {self.senate_committee: None}
#         self.senate_committee_details['status'] = None
#         self.senate_committee_details['votes'] = None
#         self.actions = None


test = TxLegeLoader(Chamber.HOUSE)
test.get_legislators(driver)