from __future__ import annotations
from typing import Self, ClassVar, NamedTuple, Optional
from inject import Binder, configure, instance
import inject

import abc

from selenium.webdriver.common.by import By
import undetected_chromedriver as uc

from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel

from driver import BuildWebDriver, BrowserDriver, BrowserWait

def get_link(value: str, _driver: BrowserDriver, by: By = By.LINK_TEXT) -> str:
    return _driver.find_element(by, value).get_attribute('href')


class ChamberTuple(NamedTuple):
    pfx: str
    full: str

class AllModelBase(abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _builder: ClassVar[BuildWebDriver] = BuildWebDriver()

    def __init__(self, builder: BuildWebDriver, **data):
        super().__init__(**data)
        self._builder = builder

    @classmethod
    def use_brave(cls) -> Self:
        cls._builder.use_brave()
        return cls

    @classmethod
    def headless(cls) -> Self:
        cls._builder.headless()
        return cls

class DBModelBase(SQLModel, AllModelBase):
    pass

class NonDBModelBase(BaseModel, AllModelBase):
    pass
