from typing import NamedTuple
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait

BrowserDriver = ChromeDriver
BrowserWait = WebDriverWait


class ChamberTuple(NamedTuple):
    pfx: str
    full: str
    member_pfx: str
    bill_pfx: str
