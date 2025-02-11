from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Any, Optional, Generator, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from txlege_bill_scraper.bases import (
    ChamberTuple,
    InterfaceBase,
    SessionDetails
)
from txlege_bill_scraper.build_logger import LogFireLogger

from .bill_list import BillListInterface
from .committees import CommitteeInterface
from .members import MemberListInterface
from .bill_details import BillDetailInterface

logfire_context = LogFireLogger.logfire_context

OutputGenerator = Union[
    Generator[Dict[str, Dict[str, Any]], None, None], Dict[str, Any], Dict[str, Dict], list[Dict]]  #type: ignore

@dataclass
class SessionInterface(InterfaceBase):
    chamber: ChamberTuple
    legislative_session: str | int
    bills: OutputGenerator = field(default_factory=dict)
    committees: OutputGenerator = field(default_factory=dict)
    members: OutputGenerator = field(default_factory=list)

    def __post_init__(self):
        interfaces = [MemberListInterface, CommitteeInterface, BillListInterface]
        for interface in interfaces:
            interface.chamber = self.chamber
            interface.legislative_session = self.legislative_session

    @LogFireLogger.logfire_method_decorator("SessionInterface.navigate_to_page")
    def navigate_to_page(self, *args, **kwargs):
        with self.driver_and_wait() as (D_, W_):
            D_.get(self._base_url)
            W_.until(
                EC.element_to_be_clickable((By.LINK_TEXT, f"{self.chamber.full}"))
            ).click()
            W_.until(lambda _: D_.find_element(By.TAG_NAME, "body")).is_displayed()

    def build_bill_list(self) -> Generator[Dict[str, Dict[str, Any]], None, None]:
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()
        self.navigate_to_page()
        return self.members

    def build_member_list(self) -> Generator[Dict[str, Dict[str, Any]], None, None]:
        self.navigate_to_page()
        self.members = MemberListInterface.fetch()
        return self.members

    def build_committee_list(self) -> Generator[Dict[str, Dict[str, Any]], None, None]:
        self.navigate_to_page()
        self.committees = CommitteeInterface.fetch()
        return self.committees

    def build_bill_details(self):
        self.navigate_to_page()
        if not self.bills:
            self.build_bill_list()
        self.bills = BillListInterface.fetch()
        return self.bills

    def fetch(self):
        self.build_bill_list()
        self.build_member_list()
        self.build_committee_list()
        self.build_bill_details()

        self.bills = {k: v for x in self.bills for k, v in x.items()}
        self.navigate_to_page()
        self.members = list(self.members)
        self.navigate_to_page()
        self.committees = {k: v for x in self.committees for k, v in x.items()}
        self.navigate_to_page()
        self.bills = {k: v for x in self.bills for k, v in x.items()}
