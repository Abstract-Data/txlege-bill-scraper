from __future__ import annotations

from src.txlege_bill_scraper.build_logger import LogFireLogger
from src.txlege_bill_scraper.bases import InterfaceBase, ChamberTuple
from .members import MemberDetailInterface, MemberListInterface
from .bill_list import BillListInterface
from .committees import CommitteeInterface
from pydantic.dataclasses import dataclass as pydantic_dataclass

logfire_context = LogFireLogger.logfire_context

@pydantic_dataclass
class SessionInterface(InterfaceBase):
    chamber: "ChamberTuple"
    legislative_session: str | int

    def __post_init__(self):
        super()._select_legislative_session()
        interfaces = [
            MemberListInterface,
            CommitteeInterface,
            BillListInterface
        ]
        for interface in interfaces:
            interface.chamber = self.chamber
            interface.legislative_session = self.legislative_session
    @classmethod
    def navigate_to_page(cls, *args, **kwargs):
        pass

    def build_bill_list(self):
        self.bills = BillListInterface.build_bill_list()

    def build_member_list(self):
        self.members = MemberListInterface.fetch_member_info()

    def build_committee_list(self):
        CommitteeInterface.navigate_to_page()
        self.committees = CommitteeInterface.create()
