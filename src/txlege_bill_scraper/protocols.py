from __future__ import annotations
from typing import NamedTuple, Final, Dict, List, Annotated, Optional, Union
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
import tomli
from bs4 import Tag as BeautifulSoupTag
from enum import Enum
from pydantic import BeforeValidator, AfterValidator, PastDate, HttpUrl

from validation_tools import get_element_text, format_datetime, check_url

BrowserDriver: Final = ChromeDriver
BrowserWait: Final = WebDriverWait

ScrapedPageElement = BeautifulSoupTag
ScrapedPageContainer = List[ScrapedPageElement]

HttpsValidatedURL = Annotated[Optional[HttpUrl], AfterValidator(check_url)]
WebElementText = Annotated[
    Optional[Union[BeautifulSoupTag, str, list]], BeforeValidator(get_element_text)
]
WebElementDate = Annotated[Optional[PastDate], BeforeValidator(format_datetime)]

CONFIG: Final[Dict] = tomli.load(open(Path(__file__).parents[0] / "tlo_urls.toml", "rb"))

class ChamberTuple(NamedTuple):
    pfx: str
    full: str
    member_pfx: str
    bill_pfx: str

class SessionDetails(NamedTuple):
    lege_session: str
    lege_session_desc: str

class TypePrefix(NamedTuple):
    BILLS: str = CONFIG['PREFIXES']['BILLS']
    MEMBERS: str = CONFIG['PREFIXES']['MEMBERS']
    COMMITTEES: str = CONFIG['PREFIXES']['COMMITTEES']

class TLOBaseUrls(NamedTuple):
    BASE: str = CONFIG['TLO-BASE-URL']
    BILL_TEXT: str = CONFIG['BILL-TEXT-BASE']
    FISCAL_NOTE: str = CONFIG['FISCAL-NOTE-BASE']
    FILED_BILLS: str = CONFIG['FILED-BILLS-LIST']

class BillDocFileType(str, Enum):
    PDF = 'PDF'
    WORD = 'WORD'
    HTML = 'HTML'
    TEXT = 'TXT'

class BillDocDescription(str, Enum):
    BILL_TEXT = 'Bill'
    BILL_VERSION = 'Bill Version'
    FISCAL_NOTE = 'Fiscal Note'
    ANALYSIS = 'Bill Analysis'
    IMPACT = 'Fiscal Impact Statement'
    WITNESS_LIST = 'Witness List'
    SUMMARY = 'Bill Summary'
    AMENDMENT = 'Amendment'

TYPE_PREFIXES = TypePrefix()
TLO_URLS = TLOBaseUrls()
HOUSE = ChamberTuple(pfx="H" , full="House", member_pfx="Rep", bill_pfx="HB")
SENATE = ChamberTuple(pfx="S", full="Senate", member_pfx="Sen", bill_pfx="SB")