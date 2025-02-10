from __future__ import annotations
from dataclasses import field
from typing import NamedTuple, Final
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait
# from .bills import (
#     BillDetailProtocol, BillActionProtocol,
#     AmendmentProtocol, BillStageProtocol,
#     CommitteeBillStatusProtocol, CommitteeVoteCountProtocol, CommitteeDetailsProtocol
# )

BrowserDriver: Final = ChromeDriver
BrowserWait: Final = WebDriverWait


class ChamberTuple(NamedTuple):
    pfx: str
    full: str
    member_pfx: str
    bill_pfx: str

class SessionDetails(NamedTuple):
    lege_session: str
    lege_session_desc: str

HOUSE = ChamberTuple(pfx="H" , full="House", member_pfx="Rep", bill_pfx="HB")
SENATE = ChamberTuple(pfx="S", full="Senate", member_pfx="Sen", bill_pfx="SB")