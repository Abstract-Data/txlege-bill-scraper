import asyncio
from dataclasses import dataclass
import abc
from typing import Self, ClassVar
import httpx
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import logfire

from txlege_bill_scraper.protocols import TLO_URLS, BillDocFileType
from interfaces.link_builders import LegislativeSessionLinkBuilder

@dataclass
class DetailScrapingInterface(abc.ABC):
    links: LegislativeSessionLinkBuilder
    timeout: ClassVar[httpx.Timeout] = httpx.Timeout(20.0, connect=20.0)  # Set timeouts for connect and read operations
    limits: ClassVar[httpx.Limits] = httpx.Limits(max_connections=20, max_keepalive_connections=10)
    semaphore: asyncio.Semaphore = asyncio.Semaphore(10)

    @classmethod
    def build_url(cls, href: str) -> str:
        new_url = urljoin(cls.links._base_url, href.replace('..', ''))
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
    def get_document_type(cls, href: str) -> BillDocFileType:
        """Determine document type based on URL and image alt text"""
        if '.pdf' in href:
            return BillDocFileType.PDF
        elif '.docx' in href:
            return BillDocFileType.WORD
        elif '.htm' in href:
            return BillDocFileType.HTML
        elif '.txt' in href:
            return BillDocFileType.TEXT


    @abc.abstractmethod
    def build_detail(self, *args, **kwargs) -> Self:
        ...

    @abc.abstractmethod
    def fetch(self, *args, **kwargs) -> Self:
        ...