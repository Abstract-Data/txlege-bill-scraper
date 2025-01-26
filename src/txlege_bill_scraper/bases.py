from __future__ import annotations
import abc


from selenium.webdriver.common.by import By
from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel

from src.txlege_bill_scraper.driver import BrowserWait, BrowserDriver, BuildWebDriver

# TODO: Figure out how to get dependency injection to work correctly.

def get_link(value: str, _driver: BrowserDriver, by: By = By.LINK_TEXT) -> str:
    return _driver.find_element(by, value).get_attribute('href')


class DriverConfigMixin:
    _builder: BuildWebDriver = BuildWebDriver()

class AllModelBase(abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DBModelBase(SQLModel, AllModelBase):
    pass

class NonDBModelBase(BaseModel, AllModelBase):
    pass

class InterfaceBase(DriverConfigMixin):
    pass