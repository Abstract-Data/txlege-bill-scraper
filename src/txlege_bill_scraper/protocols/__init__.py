from typing import NamedTuple
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait
from .bills import (
    BillDetailProtocol, BillActionProtocol, 
    AmendmentProtocol, BillStageProtocol, 
    CommitteeBillStatusProtocol, CommitteeVoteCountProtocol, CommitteeDetailsProtocol
)

BrowserDriver = ChromeDriver
BrowserWait = WebDriverWait


class ChamberTuple(NamedTuple):
    pfx: str
    full: str
    member_pfx: str
    bill_pfx: str
