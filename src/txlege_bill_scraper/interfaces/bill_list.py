from __future__ import annotations

from typing import List, Dict, Tuple
from urllib.parse import parse_qs, urlparse

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import inject

from src.txlege_bill_scraper.bases import InterfaceBase, BrowserDriver, BrowserWait
from src.txlege_bill_scraper.protocols import ChamberTuple
# from ..factories import bills as BILL_FACTORY
from src.txlege_bill_scraper.build_logger import LogFireLogger

class BillListInterface(InterfaceBase):


    @classmethod
    @LogFireLogger.logfire_method_decorator("BillListInterface.navigate_to_page")
    def navigate_to_page(cls, *args, **kwargs):
        _chamber = cls.chamber
        _lege_session_num = cls.legislative_session
        with super().driver_and_wait() as (D_, W_):
            D_.get(cls._base_url)
            FILED_BILL_REF = f"Filed {_chamber.full} Bills"
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{_chamber.full}"))).click()
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, FILED_BILL_REF)))

            filed_house_bills = D_.find_element(By.LINK_TEXT, FILED_BILL_REF).get_attribute("href")
            D_.get(filed_house_bills)

            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, FILED_BILL_REF)))

            filed_house_bills = D_.find_element(By.LINK_TEXT, FILED_BILL_REF).get_attribute("href")
            leg_sess = parse_qs(urlparse(filed_house_bills).query).get('LegSess', [''])[0]

            D_.get(filed_house_bills.replace(leg_sess, _lege_session_num))
            W_.until(EC.element_to_be_clickable((By.TAG_NAME, "table")))

    @staticmethod
    def _extract_bill_link(table_element: WebElement) -> Tuple[str, str] | None:
        """Extract bill number and URL from table element"""
        try:
            link = table_element.find_element(
                By.CSS_SELECTOR,
                "tr:first-child td:first-child a"
            )
            return link.text.strip() if link else None, link.get_attribute("href") if link else None
        except NoSuchElementException:
            return None

    @classmethod
    @LogFireLogger.logfire_method_decorator("BillListInterface._get_bill_links")
    def _get_bill_links(cls) -> List[Tuple[str, str]]:
        with super().driver_and_wait() as (D_, W_):
            W_.until(
                lambda _driver: D_.execute_script('return document.readyState') == 'complete'
            )
            find_bill_links = D_.find_elements(By.TAG_NAME, "a")
            bill_links = []
            for link in find_bill_links:
                bill_links.append(("".join(link.text.split()).strip(), link.get_attribute("href")))

            return bill_links

    @classmethod
    @LogFireLogger.logfire_method_decorator("BillListInterface._build_bill_list")
    def build_bill_list(cls) -> Dict[str, Dict[str, str]]:
        # with logfire_context(f"BillListInterface._build_bill_list({cls.chamber.full})"):
        cls.navigate_to_page()
        bill_links = cls._get_bill_links()
        bills = {}
        for bill in bill_links:
            bills[bill[0]] = {
                'bill_id': f"{cls.legislative_session}_{bill[0]}",
                'bill_url': bill[1]
            }
        return bills

    # @classmethod
    # @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    # def build_bill_details(cls,
    #                         _bill_list_id: str,
    #                         _bills: List[BILL_FACTORY.BillDetail],
    #                         _chamber: ChamberTuple,
    #                         _committees: Dict[str, BILL_FACTORY.CommitteeDetails],
    #                         _driver: BrowserDriver,
    #                         _wait: BrowserWait) -> List[BILL_FACTORY.BillDetail]:
    #     with logfire_context("BillListInterface._build_bill_details"):
    #         output_bills = []
    #         for _bill in _bills:
    #             _bill = _bills.pop()
    #             _driver.get(_bill.bill_url)
    #             _wait.until(EC.presence_of_element_located((By.ID, "Form1")))
    #
    #             # Extract bill stages
    #             BILL_FACTORY.extract_basic_details(
    #                 _bill_list_id=_bill_list_id,
    #                 _bill=_bill,
    #                 _chamber=_chamber,
    #                 _committees=_committees,
    #                 _driver=_driver)
    #             BILL_FACTORY.extract_action_history(_bill=_bill, _driver=_driver)
    #             BILL_FACTORY.create_bill_stages(_bill, _driver, _wait)
    #             BILL_FACTORY.extract_amendments(_bill, _driver)
    #             output_bills.append(_bill)
    #     return output_bills