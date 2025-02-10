from .lege_session import SessionInterface, SessionDetails

# from __future__ import annotations
#
# from pydantic.dataclasses import dataclass as pydantic_dataclass
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
#
# from txlege_bill_scraper.bases import (
#     BrowserDriver,
#     BrowserWait,
#     ChamberTuple,
#     InterfaceBase,
# )
# from txlege_bill_scraper.build_logger import LogFireLogger
# from txlege_bill_scraper.protocols import HOUSE
#
# from .bill_list import BillListInterface
# from .committees import CommitteeInterface
# from .members import MemberDetailInterface, MemberListInterface
#
# logfire_context = LogFireLogger.logfire_context
#
#
# @pydantic_dataclass
# class SessionInterface(InterfaceBase):
#     chamber: ChamberTuple
#     legislative_session: str | int
#
#     def __post_init__(self):
#         interfaces = [MemberListInterface, CommitteeInterface, BillListInterface]
#         for interface in interfaces:
#             interface.chamber = self.chamber
#             interface.legislative_session = self.legislative_session
#
#     def navigate_to_page(self, *args, **kwargs):
#         with self.driver_and_wait() as (D_, W_):
#             D_.get(self._base_url)
#             W_.until(
#                 EC.element_to_be_clickable((By.LINK_TEXT, f"{self.chamber.full}"))
#             ).click()
#
#     def build_bill_list(self):
#         self.navigate_to_page()
#         self.bills = BillListInterface.build_bill_list()
#
#     def build_member_list(self):
#         self.navigate_to_page()
#         self.members = MemberListInterface.fetch_member_info()
#
#     def build_committee_list(self):
#         self.navigate_to_page()
#         CommitteeInterface.navigate_to_page()
#         self.committees = CommitteeInterface.create()
