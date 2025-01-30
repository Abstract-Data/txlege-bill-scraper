from dataclasses import dataclass
from typing import Optional, ClassVar, Union
from pathlib import Path

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

BRAVE_PATH = Path.home() / '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'



@dataclass
class BuildWebDriver:
    OPTIONS: ClassVar[Optional[Union[ChromeOptions, BraveOptions]]] = None
    DRIVER: ClassVar[Optional[Union[ChromeDriver, BraveDriver]]] = None
    WAIT: ClassVar[Optional[WebDriverWait]] = None
    using_brave: ClassVar[bool] = False
    headless_mode: ClassVar[bool] = False
    injection_configured: ClassVar[bool] = False

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
    def build(cls) -> None:
        """Create the driver and wait right on the class."""
        cls._set_options()
        if cls.using_brave:
            cls.DRIVER = BraveDriver(options=cls.OPTIONS)
        else:
            cls.DRIVER = ChromeDriver(options=cls.OPTIONS)
        cls.WAIT = WebDriverWait(cls.DRIVER, 10)
    
    @classmethod
    def provide_driver(cls):
        """Provider function for driver (for Python Inject)"""
        if not cls.DRIVER:
            cls.build()
        return cls.DRIVER
    
    @classmethod
    def provide_wait(cls):
        """Provider function for wait instance (for Python Inject)"""
        if not cls.WAIT:
            cls.build()
        return cls.WAIT