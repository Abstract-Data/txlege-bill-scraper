from __future__ import annotations
import abc
from functools import partial
from typing import Dict, Any, Generator, Optional, ClassVar, ContextManager, Tuple
from contextlib import contextmanager
import functools
from dataclasses import dataclass, field

from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pydantic import BaseModel, ConfigDict
from sqlmodel import SQLModel
import inject
from inject import Binder, configure_once
import logfire

from .protocols import BrowserDriver, BrowserWait, ChamberTuple
from .driver import BuildWebDriver, DriverAndWaitContext
from .build_logger import LogFireLogger
from . import CONFIG

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


class DBModelBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class NonDBModelBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


@dataclass
class InterfaceBase(abc.ABC):
    chamber: ChamberTuple
    legislative_session: str | int
    bills: Dict[str, Any] = field(default_factory=dict)
    committees: Dict[str, Dict] = field(default_factory=dict)
    members: list[Dict] = field(default_factory=list)
    _base_url: ClassVar[str] = CONFIG['TLO-BASE-URL']
    _tlo_session_dropdown_value: Optional[str] = None
    def __init__(self):
        logfire.info(f"InterfaceBase initialized with {self.chamber} and {self.legislative_session}")

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def driver_and_wait(cls, _driver: BrowserDriver, _wait: BrowserWait) -> DriverAndWaitContext:
        return BuildWebDriver.driver_and_wait(_driver, _wait)

    @classmethod
    @abc.abstractmethod
    def navigate_to_page(cls, *args, **kwargs) -> None:
        ...

    @classmethod
    @LogFireLogger.logfire_method_decorator("InterfaceBase._select_legislative_session")
    def select_legislative_session(cls, identifier: Optional[str] = None) -> str:
        identifier = "cboLegSess" if not identifier else identifier
        return cls._legistative_session_selector(_field_id=identifier)

    @classmethod
    def _legistative_session_selector(cls, _field_id: str) -> [str, str]:

        with cls.driver_and_wait() as (D_, W_):
            W_.until(EC.element_to_be_clickable((By.ID, _field_id)))
            # _wait.until(EC.element_to_be_clickable((By.ID, "ddlLegislature")))
            _session_element = D_.find_element(By.ID, _field_id)
            _session_select = Select(_session_element)
            _session_options = _session_select.options
            remove_parenthesis = str.maketrans('', '', "()")
            _session_choice = next(
                (
                    x for x in _session_options
                    if (
                    x.text.translate(remove_parenthesis)
                    .startswith(str(cls.legislative_session))
                     if type(cls.legislative_session)
                        is not int
                     else str(cls.legislative_session))
                ),
                None
            )
            _selection_text = _session_choice.text
            _selection = (
                    _session_choice.text
                    .translate(remove_parenthesis)
                    .split('-')[0]
                    .strip()
                )
            _session_select.select_by_visible_text(_session_choice.text)
            D_.implicitly_wait(5)
            return _selection, _selection_text

    @staticmethod
    def _get_text_by_label(label, element, *args, **kwargs) -> Optional[str]:
        try:
            label_element = element.find_element(kwargs.get('by', By.ID), label)
            if kwargs.get('get'):
                if kwargs.get('has_text'):
                    return next(
                        (
                            x.get_attribute(
                                kwargs.get(kwargs['get'])
                            ) for x in label_element if "Bills Authored" in x.text
                        ),
                        None
                    )
                return label_element.get_attribute(kwargs['get'])
            return label_element.text
        except:
            return None

    @classmethod
    @contextmanager
    def get_text_by_label_context(cls, element) -> Generator[partial[str | None], Any, None]:
        try:
            yield functools.partial(cls._get_text_by_label, element=element)
        finally:
            pass



