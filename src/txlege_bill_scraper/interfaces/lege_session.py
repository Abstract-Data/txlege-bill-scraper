from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Any, Optional
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


@dataclass
class SessionInterface(InterfaceBase):
    chamber: ChamberTuple
    legislative_session: str | int
    bills: Dict[str, Any] = field(default_factory=dict)
    committees: Dict[str, Dict] = field(default_factory=dict)
    members: list[Dict] = field(default_factory=list)

    def __post_init__(self):
        interfaces = [MemberListInterface, CommitteeInterface, BillListInterface]
        for interface in interfaces:
            interface.chamber = self.chamber
            interface.legislative_session = self.legislative_session

    def navigate_to_page(self, *args, **kwargs):
        with self.driver_and_wait() as (D_, W_):
            D_.get(self._base_url)
            W_.until(
                EC.element_to_be_clickable((By.LINK_TEXT, f"{self.chamber.full}"))
            ).click()

    def build_bill_list(self):
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()

    def build_member_list(self):
        self.navigate_to_page()
        self.members = MemberListInterface.fetch()

    def build_committee_list(self):
        self.navigate_to_page()
        self.committees = CommitteeInterface.fetch()

    def build_bill_details(self):
        self.navigate_to_page()
        self.bills = BillDetailInterface.fetch(self.bills)

    def fetch(self):
        self.build_bill_list()
        self.build_member_list()
        self.build_committee_list()
        self.build_bill_details()
        super().close_driver()
