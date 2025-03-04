from __future__ import annotations

import asyncio
from dataclasses import dataclass
import abc
from typing import Self, ClassVar, List, ForwardRef
import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup, ResultSet as BeautifulSoupResultSet
import logfire

from models.bills import TXLegeBill, BillVersion, BillDoc, BillDocDescription
from protocols import TLO_URLS, BillDocFileType
from interfaces.link_builders import LegislativeSessionLinkBuilder

@dataclass
class DetailScrapingInterface(abc.ABC):
    links: LegislativeSessionLinkBuilder
    bill_components: ForwardRef('BillDetailScraper.components')
    timeout: ClassVar[httpx.Timeout] = httpx.Timeout(20.0, connect=20.0)  # Set timeouts for connect and read operations
    limits: ClassVar[httpx.Limits] = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(10)

    @classmethod
    def build_url(cls, href: str) -> str:
        new_url = urljoin(cls.links._base_url, href.replace('..', ''))  #type: ignore
        return new_url

    @classmethod
    async def fetch_with_retries(cls, client: httpx.AsyncClient, url: str, max_retries: int = 5) -> BeautifulSoup | None:
        retries = 0
        while retries < max_retries:
            try:
                response = await client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                return soup
            except (httpx.ConnectError, httpx.ReadTimeout):
                retries += 1
                logfire.warn(
                    f"Failed to connect to {url}, retrying {retries}/{max_retries}"
                )
                await asyncio.sleep(2)
        logfire.error(f"Failed to connect to {url} after {max_retries} attempts")
        return None

    @classmethod
    def get_document_type(cls, href: str) -> BillDocFileType | None:
        """Determine document type based on URL and image alt text"""
        if '.pdf' in href:
            return BillDocFileType.PDF
        elif '.docx' in href:
            return BillDocFileType.WORD
        elif '.htm' in href:
            return BillDocFileType.HTML
        elif '.txt' in href:
            return BillDocFileType.TEXT

    @classmethod
    def create_bill_doc(
            cls,
            links: BeautifulSoupResultSet,
            bill: TXLegeBill,
            version_info: BillVersion,
            doc_type=BillDocDescription
    ) -> List[BillDoc]:
        """
        Create a list of BillDoc objects from a BeautifulSoup ResultSet of links

        :param links: BeautifulSoupResultSet of links
        :type links: BeautifulSoupResultSet
        :param bill: TXLegeBill object
        :type bill: TXLegeBill
        :param version_info: BillVersion object
        :type version_info: BillVersion
        :param doc_type: Type[BillDocDescription] object
        :type doc_type: BillDocDescription
        :return: List of BillDoc objects
        :rtype: List[BillDoc]
        """
        _docs = []
        for link in links:
            href = link.get("href")
            if href:
                doc_type_finder = cls.get_document_type(href)
                _docs.append(
                    BillDoc(
                        bill_id=bill.id,
                        version_id=version_info.id,
                        version=version_info.version,
                        doc_url=cls.build_url(href),
                        doc_type=doc_type_finder,
                        doc_description=doc_type,
                    )
                )
        return _docs


    @abc.abstractmethod
    def build_detail(self, *args, **kwargs) -> Self:
        ...

    @abc.abstractmethod
    @logfire.instrument()
    def fetch(self, *args, **kwargs) -> Self:
        ...