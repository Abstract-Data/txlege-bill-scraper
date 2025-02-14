from dataclasses import dataclass
import abc
from typing import Self, ClassVar
import httpx
from urllib.parse import urljoin

from interfaces.link_builders.bases import LegislativeSessionLinkBuilder

@dataclass
class DetailScrapingInterface(abc.ABC):
    links: LegislativeSessionLinkBuilder
    timeout: ClassVar[httpx.Timeout] = httpx.Timeout(20.0, connect=20.0)  # Set timeouts for connect and read operations
    limits: ClassVar[httpx.Limits] = httpx.Limits(max_connections=20, max_keepalive_connections=10)

    @classmethod
    def build_url(cls, href: str) -> str:
        new_url = urljoin(cls.links._base_url, href.replace('..', ''))
        return new_url

    @classmethod
    def get_document_type(cls, href: str) -> str:
        """Determine document type based on URL and image alt text"""
        if '.pdf' in href:
            return 'pdf'
        elif '.docx' in href:
            return 'word'
        elif '.htm' in href:
            return 'html'
        elif '.txt' in href:
            return 'text'


    @abc.abstractmethod
    def build_detail(self, *args, **kwargs) -> Self:
        ...

    @abc.abstractmethod
    def fetch(self, *args, **kwargs) -> Self:
        ...