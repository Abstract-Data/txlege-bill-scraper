from dataclasses import dataclass
from typing import Optional, ClassVar
from pathlib import Path

import inject
from inject import Binder, configure
from functools import lru_cache

from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
import undetected_chromedriver as uc

BraveOptions = uc.ChromeOptions
BraveDriver = uc.Chrome
ChromeDriver = webdriver.Chrome

BraveOptions.__repr__ = lambda self: "BraveOptions"
BraveDriver.__repr__ = lambda self: "BraveDriver"
ChromeDriver.__repr__ = lambda self: "SeleniumChromeDriver"
ChromeOptions.__repr__ = lambda self: "SeleniumChromeOptions"

BrowserOptions = ChromeOptions | BraveOptions  # type: ignore
BrowserDriver = ChromeDriver | BraveDriver  # type: ignore
BrowserWait = WebDriverWait

BRAVE_PATH = Path.home() / '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
# @contextmanager
# def driver_factory(driver: BrowserDriver) -> Iterator[BrowserDriver]:
#     try:
#         yield driver
#     finally:
#         driver.quit()

@dataclass
class BuildWebDriver:
    OPTIONS: ClassVar[Optional[BrowserOptions]] = None
    DRIVER: ClassVar[Optional[BrowserDriver]] = None
    WAIT: ClassVar[Optional[WebDriverWait]] = None
    using_brave: ClassVar[bool] = False
    headless_mode: ClassVar[bool] = False
    injection_configured: bool = False


    @classmethod
    def use_brave(cls):
        """
        Use the Brave browser as the WebDriver
        :return: self
        """
        cls.using_brave = True
        return cls

    @classmethod
    def headless(cls):
        """
        Set the WebDriver to run in headless mode
        :return: self
        """
        cls.headless_mode = True
        return cls

    @classmethod
    def _set_options(cls):
        if cls.using_brave:
            if BRAVE_PATH.exists():
                options = BraveOptions()
                options.binary_location = str(BRAVE_PATH)
            else:
                raise FileNotFoundError(f"Brave Browser not found at {BRAVE_PATH}")
        else:
            options = ChromeOptions()

        options.add_argument("--window-size=1920,1080")
        options.page_load_strategy = "none"

        if cls.headless_mode:
            options.add_argument("--headless=True")
        cls.OPTIONS = options
        return cls

    @classmethod
    def build(cls):
        cls._set_options()
        cls.DRIVER = (
            BraveDriver(options=cls.OPTIONS)
            if cls.using_brave
            else ChromeDriver(options=cls.OPTIONS)
        )
        _wait_obj = WebDriverWait(cls.DRIVER, 10)
        _wait_obj.__class__.__repr__ = lambda self: f"WebDriverWait({cls.DRIVER.__repr__()}, 10)"
        cls.WAIT = _wait_obj
        return cls