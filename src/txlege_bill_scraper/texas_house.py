import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import Final, Dict
import tomli
from pathlib import Path

with open(Path(__file__).parent / "tlo_urls.toml", "rb") as config:
    urls: Dict = tomli.load(config)


LEGISLATIVE_SESSION: str = "87R"
BILL_TYPE: str = "HB" or "SB"
BILL_NUMBER: int = 1
TLO_URL: Final = urls.get("MAIN-TLO-URL")
TLO_MEMBER_BILL_LIST_URL: Final = TLO_URL + urls["MEMBER-URLS"]["BILL-LIST"]
TLO_CHAMBER_LIST: Final = TLO_URL + urls["CHAMBER-URLS"]["MEMBER-LIST"]


@dataclass
class TxLegeLoader:
    chamber: str
    lege_session: str = field(default=LEGISLATIVE_SESSION)
    __chamber_list_url = TLO_CHAMBER_LIST

    def __post_init__(self):
        self.page = requests.get(self.URL).text
        self.members: list = self.get_legislators()

    def __repr__(self):
        return f"Texas {self.chamber} Members for {self.lege_session.upper()} Legislative Session"

    @property
    def URL(self):
        match self.chamber.title():
            case "House":
                _chamber = "H"
            case "Senate":
                _chamber = "S"
            case _:
                raise ValueError("Chamber must be 'House' or 'Senate'")

        return self.__chamber_list_url.format(_chamber)

    def get_legislators(self) -> list:
        _soup = BeautifulSoup(self.page, "html.parser")
        _tables = _soup.find_all("table", id="dataListMembers")
        _members = {}
        for table in _tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                for cell in cells:
                    if cell.find("a"):
                        if self.chamber == "house":
                            _prefix = "Representative"
                        else:
                            _prefix = "Senator"
                        _member = LegislativeMember(
                            prefix=_prefix,
                            last_name=cell.find("a").text.strip(),
                            tlo_id=cell.find("a")["href"].split("=")[-1],
                            session_num=self.lege_session,
                        )
                        _members.update(
                            {f"{_member.prefix} {_member.last_name}": _member}
                        )
        return _members


@dataclass
class LegislativeMember:
    prefix: str
    last_name: str
    tlo_id: str
    session_num: str

    def __repr__(self):
        return f"TLO Desc for: {self.prefix} {self.last_name}"

    def __post_init__(self):
        self.__bill_url = TLO_MEMBER_BILL_LIST_URL.format(
            self.session_num, self.tlo_id
        )
        self.legislation = self.fetch_legislation(self.__bill_url)

    def fetch_legislation(self, __url=None):
        _page = requests.get(__url)
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


@dataclass
class BillDetails:
    chamber: str
    number: int
    _session: str = LEGISLATIVE_SESSION

    def __post_init__(self):
        self.last_action = None
        self.caption_version = None
        self.caption_text = None
        self.authors = None
        self.coauthors = None
        self.sponsors = None
        self.subjects = None
        self.companion = None
        self.house_committee = None
        self.house_committee_details = {self.house_committee: None}
        self.house_committee_details['status'] = None
        self.house_committee_details['votes'] = None
        self.senate_committee = None
        self.senate_committee_details = {self.senate_committee: None}
        self.senate_committee_details['status'] = None
        self.senate_committee_details['votes'] = None
        self.actions = None