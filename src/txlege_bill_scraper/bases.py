from __future__ import annotations
import abc


from selenium.webdriver.common.by import By
from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel
from inject import Binder, configure_once

from src.txlege_bill_scraper.types import BrowserDriver, BrowserWait
from src.txlege_bill_scraper.driver import BuildWebDriver

# TODO: Figure out how to get dependency injection to work correctly.

def get_link(value: str, _driver: BrowserDriver, by: By = By.LINK_TEXT) -> str:
    return _driver.find_element(by, value).get_attribute('href')

BuildWebDriver()

def configure_injection() -> None:
    """Call this once at the start of your program to set up injection."""
    def bindings(binder: Binder) -> None:
        # Bind them using the provider methods 
        binder.bind_to_provider(BrowserDriver, BuildWebDriver.provide_driver)
        binder.bind_to_provider(BrowserWait, BuildWebDriver.provide_wait)
    configure_once(bindings)

configure_injection()

class AllModelBase(abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class DBModelBase(SQLModel, AllModelBase):
    pass

class NonDBModelBase(BaseModel, AllModelBase):
    pass

class InterfaceBase(abc.ABC):
    pass

