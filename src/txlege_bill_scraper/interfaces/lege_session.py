from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, Any, Optional, Generator, Union, Self
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import httpx

from interfaces.link_builders import (
    ChamberTuple,
    LegislativeSessionLinkBuilder,
    SessionDetails,
    BillListInterface,
    MemberListInterface,
    CommitteeInterface
)
from interfaces.scrapers import DetailScrapingInterface, MemberDetailScraper, BillDetailScraper
from txlege_bill_scraper.build_logger import LogFireLogger
from .bill_details import BillDetailInterface

logfire_context = LogFireLogger.logfire_context

OutputGenerator = Union[
    Dict[str, Dict[str, Any]], Dict[str, Any], Dict[str, Dict], list[Dict], list[tuple[str, str]]]  #type: ignore

@dataclass
class SessionInterfaceBase(LegislativeSessionLinkBuilder):
    chamber: ChamberTuple
    legislative_session: str | int | SessionDetails
    bills: OutputGenerator = field(default_factory=dict)
    committees: OutputGenerator = field(default_factory=dict)
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

    @LogFireLogger.logfire_method_decorator("SessionInterface.navigate_to_page")
    def navigate_to_page(self, *args, **kwargs):
        with self.driver_and_wait() as (D_, W_):
            D_.get(self._base_url)
            W_.until(
                EC.element_to_be_clickable((By.LINK_TEXT, f"{self.chamber.full}"))
            ).click()
            W_.until(lambda _: D_.find_element(By.TAG_NAME, "body")).is_displayed()

    def build_bill_list(self) -> Self:
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()
        return self

    def build_member_list(self) -> Self:
        self.navigate_to_page()
        self.members = MemberListInterface.fetch()
        return self

    def build_committee_list(self) -> Self:
        self.navigate_to_page()
        self.committees = CommitteeInterface.fetch()
        return Self

    def build_bill_details(self) -> Self:
        if not self.bills:
            self.build_bill_list()
        self.navigate_to_page()
        self.bills = BillListInterface.fetch()
        return self

    def fetch(self):
        self.build_bill_list()
        self.build_member_list()
        self.build_committee_list()

class SessionDetailInterface(DetailScrapingInterface):

    def __init__(self, chamber: ChamberTuple, legislative_session: str | int):
        self.links = SessionInterfaceBase(chamber, legislative_session)
        DetailScrapingInterface.links = self.links
        BillDetailScraper.links = self.links



    async def build_detail(self):
        semaphore = asyncio.Semaphore(10)
        async with httpx.AsyncClient(timeout=self.timeout, limits=self.limits) as client:
            member_task = asyncio.create_task(
                MemberDetailScraper.fetch(self.links.members, _client=client, _sem=semaphore))
            bill_task = asyncio.create_task(
                BillDetailScraper.fetch(self.links.bills, _client=client, _sem=semaphore))

            self.links.members = await member_task
            self.links.bills = await bill_task
        return self

    def fetch(self):
        asyncio.run(self.build_detail())
        return self
