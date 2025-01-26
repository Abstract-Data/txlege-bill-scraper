from __future__ import annotations
from typing import Dict
import tomli
from pathlib import Path

from selenium.webdriver.common.by import By

from legislator import LegislatorBase
from types_ import ChamberTuple
from driver import BrowserDriver
from bases import NonDBModelBase
from bills import BillList


with open(Path(__file__).parent / "tlo_urls.toml", "rb") as config:
    urls: Dict = tomli.load(config)

TLO_MAIN_URL = urls.get("MAIN-TLO-URL")
TLO_CHAMBER_LIST = TLO_MAIN_URL + urls["CHAMBER-URLS"]["MEMBER-LIST"]

LEGISLATIVE_SESSION: str = "87R"

MEMBER_BILL_TYPE_URL = "https://capitol.texas.gov/reports/report.aspx?LegSess={session}}&ID={bill_writer_type}&Code={member_id}"

def get_link(value: str, _driver: BrowserDriver, by: By = By.LINK_TEXT) -> str:
    return _driver.find_element(by, value).get_attribute('href')


# class TxLegeLoader(NonDBModelBase):
#     chamber: ChamberTuple
#     lege_session: str = PydanticField(default=LEGISLATIVE_SESSION)
#     url: HttpUrl = PydanticField(default=TLO_CHAMBER_LIST)
#     page: Any = PydanticField(init=False)
#     members: list = PydanticField(init=False)
#
#     def __repr__(self):
#         return f"Texas {self.chamber} Members for {self.lege_session.upper()} Legislative Session"
#
#     @autoparams()
#     def get_legislators(self, _driver: BrowserDriver) -> Self:
#         _driver.get("https://capitol.texas.gov/Home.aspx")
#         wait = WebDriverWait(_driver, 10)
#         wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House"))).click()
#         wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House Members"))).click()
#         wait.until(EC.presence_of_element_located((By.ID, "content"))).click()
#         member_list = _driver.find_element(By.ID, "content")
#         links = member_list.find_elements(By.TAG_NAME, "a")
#         member_links = iter(x.get_attribute("href") for x in links)
#         _member_gen = [LegislatorBase(id=x.split('=')[-1], member_url=x) for x in member_links]
#         self.members = [x.fetch_member_details().fetch_legislation_details(_driver) for x in _member_gen]
#         return self


# class LegislativeMember(DBModelBase):
#     prefix: str
#     last_name: str
#     tlo_id: str
#     legislation: Dict[str, Dict[str, Any]] = field(default_factory=dict)
#     page_text: Any = field(init=False)
#     member_url: HttpUrl = None
#
#     def __repr__(self):
#         return f"TLO Desc for: {self.prefix} {self.last_name}"
#
#     def __post_init__(self):
#         _session_num = next(iter(self.legislation))
#         self.__bill_url = TLO_MEMBER_BILL_LIST_URL.format(
#             _session_num, self.tlo_id
#         )
#         self.legislation[_session_num] = self.fetch_legislation(self.__bill_url)
#
#     def fetch_legislation(self, __url=None) -> Dict[str, Dict[str, Any]]:
#         _page = requests.get(__url)
#         self.page_text = _page.text
#         self.member_url = HttpUrl(_page.url)
#         _soup = BeautifulSoup(_page.content, "html.parser")
#         _tables = _soup.find_all("table")
#         bills = {}
#         for table in _tables:
#             bill_details = {}
#             _sections = [x for x in table.find_all("tr")]
#             _bill_no = _sections[0].find_all("td")[0].text
#             if len(_sections) >= 3:
#                 bill_details.update(
#                     {
#                         _sections[0]
#                         .find_all("td")[1]
#                         .text.replace(":", ""): [
#                             x.strip()
#                             for x in _sections[0].find_all("td")[2].text.split("|")
#                         ]
#                     }
#                 )
#                 bill_details.update(
#                     {
#                         _sections[1]
#                         .find_all("td")[1]
#                         .text.replace(":", ""): [
#                             x.strip()
#                             for x in _sections[1].find_all("td")[2].text.split("|")
#                         ]
#                     }
#                 )
#                 bill_details.update(
#                     {
#                         _sections[2]
#                         .find_all("td")[1]
#                         .text.replace(":", "")
#                         .strip(): _sections[2]
#                         .find_all("td")[2]
#                         .text
#                     }
#                 )
#                 if len(_sections) == 4:
#                     bill_details.update(
#                         {
#                             _sections[3]
#                             .find_all("td")[1]
#                             .text.replace(":", ""): _sections[3]
#                             .find_all("td")[2]
#                             .text
#                         }
#                     )
#             bills.update({_bill_no: bill_details})
#         return bills
#
#     def fiscal_notes(self):
#         # TODO: Build reader to pull fiscal notes from TLO for each bill number.
#         if self.legislation:
#             fiscal_notes = {}
#             for bill, details in self.legislation.items():
#                 if details.get("Fiscal Note"):
#                     fiscal_notes.update({bill: details.get("Fiscal Note")})
#             return fiscal_notes
#
#     def get_bill(self, chamber, number):
#         return self.legislation.get(f"{chamber.upper()} {number}")


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


# test = TxLegeLoader(Chamber.HOUSE)
# test.get_legislators(driver)
HOUSE = ChamberTuple(pfx="H" , full="House", member_pfx="Rep", bill_pfx="HB")
house_bills = BillList(chamber=HOUSE)
house_bills.get_bill_list()

# TODO: Deal with BillDetails references in Bill Interface Module to avoid ciruclar imports.
# house_bills.generate_bills()