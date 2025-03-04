from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Any, Optional, Generator, Union, Self, List
import asyncio

import logfire
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import httpx

from interfaces.link_builders import (
    LegislativeSessionLinkBuilder,
    BillListInterface,
    MemberListInterface,
    CommitteeInterface,
)
from protocols import ChamberTuple, SessionDetails, BillDocFileType
from interfaces.scrapers import (
    DetailScrapingInterface,
    MemberDetailScraper,
    BillDetailScraper,
)
from models.bills import TXLegeBill, CommitteeDetails
from models.members import MemberDetails


OutputGenerator = Union[
    Dict[str, Dict[str, Any]],
    Dict[str, Any],
    Dict[str, Dict],
    list[Dict],
    list[tuple[str, str]],
]  # type: ignore


@dataclass
class SessionInterfaceBase(LegislativeSessionLinkBuilder):
    chamber: ChamberTuple
    legislative_session: str | int | SessionDetails
    bills: Dict[str, TXLegeBill] = field(default_factory=dict)
    committees: Dict[str, CommitteeDetails] = field(default_factory=dict)
    members: OutputGenerator = field(default_factory=list)

    def __init__(self, chamber: ChamberTuple, legislative_session: str | int):
        super().__init__(chamber, legislative_session)
        self.chamber = chamber
        self.legislative_session = legislative_session
        interfaces = [MemberListInterface, CommitteeInterface, BillListInterface]
        for interface in interfaces:
            interface.chamber = self.chamber
            interface.legislative_session = self.legislative_session
            interface.lege_session_id = self.lege_session_id

    def get_links(self):
        pass

    def navigate_to_page(self, *args, **kwargs):
        with self.driver_and_wait() as (D_, W_):
            D_.get(self._base_url)
            W_.until(
                EC.element_to_be_clickable((By.LINK_TEXT, f"{self.chamber.full}"))
            ).click()
            W_.until(lambda _: D_.find_element(By.TAG_NAME, "body")).is_displayed()

    @logfire.instrument()
    def build_bill_list(self) -> Self:
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()
        return self

    @logfire.instrument()
    def build_member_list(self) -> Self:
        self.navigate_to_page()
        self.members = MemberListInterface.fetch()
        return self

    @logfire.instrument()
    def build_committee_list(self) -> Self:
        self.navigate_to_page()
        self.committees = CommitteeInterface.fetch()
        return Self

    @logfire.instrument()
    def build_bill_details(self) -> Self:
        if not self.bills:
            self.build_bill_list()
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()
        return self

    @logfire.instrument()
    def fetch(self):
        self.build_bill_list()
        self.build_member_list()
        self.build_committee_list()

class SessionDetailInterface(DetailScrapingInterface):
    links: Optional[SessionInterfaceBase] = None
    members: List[MemberDetails] = field(default_factory=list)
    # bills: BillDetailScraper.components = BillDetailScraper.components

    def __init__(self, chamber: ChamberTuple, legislative_session: str | int):
        self.links = SessionInterfaceBase(chamber, legislative_session)
        DetailScrapingInterface.links = self.links
        DetailScrapingInterface.bill_components = BillDetailScraper.components

    async def build_detail(self):
        async with httpx.AsyncClient(
            timeout=self.timeout, limits=self.limits
        ) as client:
            bill_task = asyncio.create_task(
                BillDetailScraper.fetch(
                    self.links.bills, _client=client, _sem=self.semaphore
                )
            )
            member_task = asyncio.create_task(
                MemberDetailScraper.fetch(
                    self.links.members, _client=client, _sem=self.semaphore
                )
            )

            self.members = await member_task
            self.links.members = {
                k: v for k, v in self.links.members.items() if k not in self.members
            }
            # self.links.bills = await bill_task
            await bill_task
            # Remove bills list from links.bills that were processed
            self.links.bills = {
                k: v for k, v in self.links.bills.items() if k not in self.bill_components.bills
            }
        return self

    @logfire.instrument()
    def fetch(self):
        asyncio.run(self.build_detail())
        return self
