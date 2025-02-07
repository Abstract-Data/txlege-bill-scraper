from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, ClassVar, Union, ContextManager, Any, Generator, Tuple
from pathlib import Path
from contextlib import contextmanager, AbstractContextManager

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
import undetected_chromedriver as uc
from selenium.webdriver.support.wait import WebDriverWait
from undetected_chromedriver import Chrome

BraveOptions = uc.ChromeOptions
BraveDriver = uc.Chrome
ChromeDriver = webdriver.Chrome

BraveOptions.__repr__ = lambda self: "BraveOptions"
BraveDriver.__repr__ = lambda self: "BraveDriver"
ChromeDriver.__repr__ = lambda self: "SeleniumChromeDriver"
ChromeOptions.__repr__ = lambda self: "SeleniumChromeOptions"

BRAVE_PATH = Path.home() / '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'

DriverAndWaitContext = [AbstractContextManager[Union[ChromeDriver, BraveDriver]], AbstractContextManager[WebDriverWait]]

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

    @classmethod
    @contextmanager
    def driver_context(cls, driver: Optional[ChromeDriver]) -> Generator[WebDriver | Chrome | None, Any, None]:
        """Context manager for the driver."""
        try:
            yield cls.DRIVER if not driver else driver
        finally:
            pass

    @classmethod
    @contextmanager
    def wait_context(cls, wait: Optional[WebDriverWait]) -> Generator[WebDriverWait | None, Any, None]:
        """Context manager for the wait instance."""
        try:
            yield cls.WAIT if not wait else wait
        finally:
            pass


    @classmethod
    @contextmanager
    def driver_and_wait(cls, _driver: WebDriver, _wait: WebDriverWait) -> DriverAndWaitContext:
        with cls.driver_context(_driver) as driver_:
            with cls.wait_context(_wait) as wait_:
                yield driver_, wait_

    @classmethod
    def close_driver(cls, driver: Optional[ChromeDriver]) -> None:
        """Manually close the driver when you're done with it"""
        return driver.quit() if driver else cls.DRIVER.quit()