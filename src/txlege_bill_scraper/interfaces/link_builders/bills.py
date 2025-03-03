from __future__ import annotations

from typing import Dict, List, Tuple, Generator, Self
from urllib.parse import parse_qs, urlparse, urljoin
import httpx
import logfire
from bs4 import BeautifulSoup

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

# from txlege_bill_scraper.protocols import ChamberTuple, TypePrefix
# from txlege_bill_scraper.factories import bills as BILL_FACTORY
from protocols import TLO_URLS
from models.bills import TXLegeBill
from .bases import LegislativeSessionLinkBuilder

class BillListInterface(LegislativeSessionLinkBuilder):
    _response: httpx.Response = None

    @classmethod
    def navigate_to_page(cls, *args, **kwargs) -> Self:
        _chamber = cls.chamber
        _lege_session_num = cls.legislative_session

        if not cls._use_scrape_fallback:
            try:
                request = httpx.get(
                    urljoin(
                        cls._base_url,
                        TLO_URLS.FILED_BILLS
                        .format(
                            chamber_fullname=_chamber.full,
                            session=f"{cls.legislative_session.lege_session}{cls.legislative_session.lege_session_desc}"
                            )
                    )
                )
                cls._response = request
                return cls
            except Exception as e:
                logfire.error(f"Error: {e}")
                cls._use_scrape_fallback = True

        if cls._use_scrape_fallback:
            with super().driver_and_wait() as (D_, W_):
                FILED_BILL_REF = f"Filed {_chamber.full} Bills"
                W_.until(EC.element_to_be_clickable((By.LINK_TEXT, FILED_BILL_REF)))
                D_.find_element(By.LINK_TEXT, FILED_BILL_REF).click()

                # Select Appropriate Legislative Session
                _, cls._tlo_session_dropdown_value = super().select_legislative_session()
                W_.until(EC.element_to_be_clickable((By.LINK_TEXT, FILED_BILL_REF)))

                filed_house_bills = D_.find_element(
                    By.LINK_TEXT, FILED_BILL_REF
                ).get_attribute("href")
                D_.get(filed_house_bills)

    @classmethod
    def get_links(cls) -> Dict[str, TXLegeBill]:
        if cls._use_scrape_fallback:
            with super().driver_and_wait() as (D_, W_):
                W_.until(
                    lambda _driver: D_.execute_script("return document.readyState")
                    == "complete"
                )
                find_bill_links = D_.page_source
        elif cls._response:
            find_bill_links = cls._response
        else:
            raise Exception("No response object found")

        soup = BeautifulSoup(find_bill_links, "html.parser")
        find_bill_links = soup.find_all("a")

        bill_links = {}
        for link in find_bill_links:
            link_url = link.get("href")
            _bill_number = parse_qs(urlparse(link_url).query).get(
                "Bill", [""]
            )[0]
            bill_links[_bill_number] = TXLegeBill(
                legislative_session=cls.lege_session_id,
                bill_number = _bill_number.replace(" ", ""),
                bill_url = link_url,
            )
        return bill_links
