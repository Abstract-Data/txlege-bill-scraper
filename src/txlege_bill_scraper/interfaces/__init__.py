from src.txlege_bill_scraper.bases import InterfaceBase
from .members import MemberDetailInterface, MemberListInterface
from .bill_list import BillListInterface
from .committees import CommitteeInterface
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class SessionInterface(InterfaceBase):

    def __post_init__(self):
        self._select_legislative_session()
        interfaces = [
            MemberListInterface,
            CommitteeInterface,
            BillListInterface
        ]
        for interface in interfaces:
            interface.chamber = self.chamber
            interface.legislative_session = self.legislative_session

    def build_bill_list(self):
        self.bills = BillListInterface.build_bill_list()

    def build_member_list(self):
        self.members = MemberListInterface.fetch_member_info()

    def build_committee_list(self):
        CommitteeInterface._navigate_to_committee_page()
        self.committees = CommitteeInterface.create()
