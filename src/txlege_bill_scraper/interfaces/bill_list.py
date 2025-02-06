from __future__ import annotations

from typing import List, Dict, Tuple
from urllib.parse import parse_qs, urlparse

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import inject

from ..bases import InterfaceBase, BrowserDriver, BrowserWait
from ..protocols import ChamberTuple
from ..factories import bills as BILL_FACTORY
from ..build_logger import LogFireLogger


logfire_context = LogFireLogger.logfire_context

class BillListInterface(InterfaceBase):


    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _navigate_to_bill_page(
            cls,
            _chamber: ChamberTuple,
            _lege_session_num: str,
            _driver: BrowserDriver,
            _wait: BrowserWait):

        with logfire_context(f"BillListInterface._navigate_to_bill_page({_chamber.full})") as ctx:
            ctx.set_attribute("txlege", _lege_session_num)
            ctx.set_attribute("chamber", _chamber.full)
            ctx.set_attribute("used_url", "https://capitol.texas.gov/Home.aspx")

            _driver.get("https://capitol.texas.gov/Home.aspx")
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{_chamber.full}"))).click()
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"Filed {_chamber.full} Bills")))

            filed_house_bills = _driver.find_element(By.LINK_TEXT, f"Filed {_chamber.full} Bills").get_attribute("href")
            _driver.get(filed_house_bills)

            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"Filed {_chamber.full} Bills")))

            filed_house_bills = _driver.find_element(By.LINK_TEXT, f"Filed {_chamber.full} Bills").get_attribute("href")
            leg_sess = parse_qs(urlparse(filed_house_bills).query).get('LegSess', [''])[0]

            _driver.get(filed_house_bills.replace(leg_sess, _lege_session_num))
            _wait.until(EC.element_to_be_clickable((By.TAG_NAME, "table")))

    @staticmethod
    def _extract_bill_link(table_element: WebElement) -> Tuple[str, str] | None:
        """Extract bill number and URL from table element"""
        try:
            link = table_element.find_element(
                By.CSS_SELECTOR,
                "tr:first-child td:first-child a"
            )
            return link.text.strip(), link.get_attribute("href")
        except NoSuchElementException:
            return None

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _get_bill_links(cls, _chamber: ChamberTuple, _driver: BrowserDriver, _wait: BrowserWait) -> List[Tuple[str, str]]:
        _wait.until(
            lambda _driver: _driver.execute_script('return document.readyState') == 'complete'
        )
        bill_tables = _driver.find_elements(By.TAG_NAME, "table")
        return [link for table in bill_tables
                if (link := cls._extract_bill_link(table))]

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def build_bill_list(
            cls,
            chamber: ChamberTuple,
            lege_session: str,
            bill_list_id: str,
            _driver: BrowserDriver,
            _wait: BrowserWait) -> List[BILL_FACTORY.BillDetail]:
        with logfire_context(f"BillListInterface._build_bill_list({chamber.full})"):
            cls._navigate_to_bill_page(_chamber=chamber, _lege_session_num=lege_session)
            bill_links = cls._get_bill_links(_chamber=chamber)
            bills = []
            for bill in bill_links:
                _detail = (
                    BILL_FACTORY
                    .create_bill_detail(
                        _bill_list_id=bill_list_id,
                        _bill_number=bill[0],
                        _bill_url=bill[1]
                    )
                )
                bills.append(_detail)
        return bills

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def build_bill_details(cls,
                            _bill_list_id: str,
                            _bills: List[BILL_FACTORY.BillDetail],
                            _chamber: ChamberTuple,
                            _committees: Dict[str, BILL_FACTORY.CommitteeDetails],
                            _driver: BrowserDriver,
                            _wait: BrowserWait) -> List[BILL_FACTORY.BillDetail]:
        with logfire_context("BillListInterface._build_bill_details"):
            output_bills = []
            for _bill in _bills:
                _bill = _bills.pop()
                _driver.get(_bill.bill_url)
                _wait.until(EC.presence_of_element_located((By.ID, "Form1")))

                # Extract bill stages
                BILL_FACTORY.extract_basic_details(
                    _bill_list_id=_bill_list_id,
                    _bill=_bill,
                    _chamber=_chamber,
                    _committees=_committees,
                    _driver=_driver)
                BILL_FACTORY.extract_action_history(_bill=_bill, _driver=_driver)
                BILL_FACTORY.create_bill_stages(_bill, _driver, _wait)
                BILL_FACTORY.extract_amendments(_bill, _driver)
                output_bills.append(_bill)
        return output_bills