from typing import NamedTuple, Union
from undetected_chromedriver import ChromeOptions as BraveOptions, Chrome as BraveDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver import Chrome as ChromeDriver
from selenium.webdriver.support.ui import WebDriverWait

BrowserOptions = Union[ChromeOptions, BraveOptions]
BrowserDriver = Union[ChromeDriver, BraveDriver]
BrowserWait = WebDriverWait


class ChamberTuple(NamedTuple):
    pfx: str
    full: str
    member_pfx: str
    bill_pfx: str
