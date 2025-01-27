from __future__ import annotations
from typing import List, Optional, Dict, Tuple
import re
from contextlib import contextmanager, ExitStack
from pathlib import Path

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


import pandas as pd
import inject
import logfire
from src.txlege_bill_scraper.bases import InterfaceBase, BrowserDriver, BrowserWait
from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.types.bills import BillDetailProtocol, BillStageProtocol
from src.txlege_bill_scraper.factories.bills import create_bill_detail, create_bill_stages, create_amendment

logfire.configure(service_name=Path(__file__).stem)
LOGFIRE_CONTEXTS = []

@contextmanager
def logfire_context(value: str):
    LOGFIRE_CONTEXTS.append(value)
    try:
        with ExitStack() as stack:
            # Enter all contexts (including the newly added one)
            for context_name in reversed(LOGFIRE_CONTEXTS):
                stack.enter_context(logfire.span(context_name))
                yield
    finally:
        # Remove the one we added
        LOGFIRE_CONTEXTS.pop()

class BillDetailInterface(InterfaceBase):

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def fetch_bill_details(cls, bill: BillDetailProtocol, _driver: BrowserDriver, _wait: BrowserWait) -> BillDetailProtocol:
        _driver.get(bill.bill_url)
        _wait.until(EC.presence_of_element_located((By.ID, "Form1")))

        # Extract bill stages
        cls._extract_basic_details(_driver)
        cls._extract_action_history(_driver)
        bill.stages = cls._extract_bill_stages(_driver)

        # Get amendments page
        amend_url = bill.bill_url.replace("History.aspx", "Amendments.aspx")
        _driver.get(amend_url)
        cls._extract_amendments(_driver)
        return bill

    @classmethod
    @inject.params(_driver=BrowserDriver)
    def _extract_basic_details(cls, bill: BillDetailProtocol, _driver: BrowserDriver) -> BillDetailProtocol:
        """Extract basic bill information"""
        # Last Action
        last_action = cls._get_cell_text(_driver, "cellLastAction")
        bill.last_action_dt = re.compile(r'\d{2}/\d{2}/\d{4}').match(last_action).group() if last_action else None

        # Caption Version & Text
        bill.status = cls._get_cell_text(_driver, "cellCaptionVersion")
        bill.caption = cls._get_cell_text(_driver, "cellCaptionText")
        return bill

    @classmethod
    @inject.params(_driver=BrowserDriver)
    def _extract_action_history(cls, bill: BillDetailProtocol, _driver: BrowserDriver) -> BillDetailProtocol:
        """Extract bill action history"""
        try:
            action_rows = _driver.find_elements(By.CSS_SELECTOR, "#usrBillInfoActions_tblActions + table tr:not(:first-child)")

            actions = []
            for row in action_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 6:
                    action = {
                        'Chamber': cells[0].text.strip(),
                        'Description': cells[1].text.strip(),
                        'Comment': cells[2].text.strip(),
                        'Date': cells[3].text.strip(),
                        'Time': cells[4].text.strip(),
                        'Journal_Page': cells[5].text.strip()
                    }
                    actions.append(action)

            bill.action_list = pd.DataFrame(actions)
        except NoSuchElementException:
            bill.action_list = pd.DataFrame()
        return bill

    @classmethod
    @inject.params(_driver=BrowserDriver)
    def _get_cell_text(cls, _driver: BrowserDriver, cell_id: str) -> Optional[str]:
        """Helper method to safely get cell text"""
        try:
            return _driver.find_element(By.ID, cell_id).text.strip()
        except NoSuchElementException:
            return None

    @classmethod
    @inject.params(_driver=BrowserDriver)
    def _extract_amendments(cls, bill: BillDetailProtocol, _driver: BrowserDriver) -> BillDetailProtocol:
        """Extract all amendments and their associated documents"""
        try:
            # Check if any amendments exist
            amendment_count = _driver.find_element(By.ID, "usrBillInfoAmendments_lblAmendments").text
            if "0" in amendment_count:
                bill.amendments = []
                return

            amendment_table = _driver.find_element(By.CSS_SELECTOR, "table[bordercolor='#d0d0d0']")
            if not amendment_table:
                bill.amendments = []
                return

            amendment_rows = amendment_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            if not amendment_rows:
                bill.amendments = []
                return

            amendments = []
            for row in amendment_rows:
                try:
                    amendment = create_amendment(row)
                    amendments.append(amendment)
                except (NoSuchElementException, IndexError) as e:
                    continue

            bill.amendments = amendments
        except Exception as e:
            bill.amendments = []
        return bill

    @classmethod
    @inject.params(_driver=BrowserDriver)
    def _extract_bill_stages(cls, _driver: BrowserDriver) -> List[BillStageProtocol]:
        return create_bill_stages(cls, _driver)

    @classmethod
    def _get_link_if_exists(cls, row: WebElement, col_index: int) -> Optional[str]:
        """Helper to safely get href from cell if link exists"""
        try:
            link = row.find_element(By.CSS_SELECTOR, f"td:nth-child({col_index}) a")
            return link.get_attribute("href")
        except NoSuchElementException:
            return None




class BillListInterface(InterfaceBase):


    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _navigate_to_bill_page(cls, _chamber: ChamberTuple, _driver: BrowserDriver, _wait: BrowserWait):
        with logfire_context(f"BillListInterface._navigate_to_bill_page({_chamber.full})"):
            _driver.get("https://capitol.texas.gov/Home.aspx")
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{_chamber.full}"))).click()
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"Filed {_chamber.full} Bills")))
            filed_house_bills = _driver.find_element(By.LINK_TEXT, f"Filed {_chamber.full} Bills").get_attribute("href")
            _driver.get(filed_house_bills)
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"Filed {_chamber.full} Bills")))
            filed_house_bills = _driver.find_element(By.LINK_TEXT, f"Filed {_chamber.full} Bills").get_attribute("href")
            _driver.get(filed_house_bills)
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
    def _build_bill_list(cls, chamber: ChamberTuple, _driver: BrowserDriver, _wait: BrowserWait) -> Dict[str, BillDetailProtocol]:
        with logfire_context(f"BillListInterface._build_bill_list({chamber.full})"):
            cls._navigate_to_bill_page(_chamber=chamber)
            bill_links = cls._get_bill_links(_chamber=chamber)
            bills = {}
            bills_checked = logfire.metric_counter("bills_created")
            for bill in bill_links:
                _detail = create_bill_detail(bill_number=bill[0], bill_url=bill[1])
                bills[_detail.bill_number] = _detail
                bills_checked.add(1)
        return bills

    @classmethod
    def _build_bill_details(cls, bills: Dict[str, BillDetailProtocol]) -> Dict[str, BillDetailProtocol]:
        with logfire_context("BillListInterface._build_bill_details"):
            bills_checked = logfire.metric_counter("bills_checked")
            for bill in bills:
                try:
                    bills[bill] = BillDetailInterface.fetch_bill_details(bills[bill])
                    bills_checked.add(1)
                except Exception as e:
                    logfire.error(f"Error fetching details for bill {bill}: {e}")
        return bills