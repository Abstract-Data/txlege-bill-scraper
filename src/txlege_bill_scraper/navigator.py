from __future__ import annotations
from typing import List, Optional, Dict, Self, Tuple, ForwardRef
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException

import inject
import pandas as pd
from bases import InterfaceBase, BrowserDriver, BrowserWait, BuildWebDriver
from types_ import ChamberTuple


BillDetail = ForwardRef("BillDetail")
BillStage = ForwardRef("BillStage")
Amendment = ForwardRef("Amendment")

class BillDetailInterface(InterfaceBase):

    def fetch_bill_details(self, bill: BillDetail, _driver: BrowserDriver, _wait: BrowserWait) -> BillDetail:
        _driver.get(bill.bill_url)
        _wait.until(EC.presence_of_element_located((By.ID, "Form1")))

        # Extract bill stages
        self._extract_basic_details(_driver)
        self._extract_action_history(_driver)
        bill.stages = self._extract_bill_stages(_driver)

        # Get amendments page
        amend_url = bill.bill_url.replace("History.aspx", "Amendments.aspx")
        _driver.get(amend_url)
        self._extract_amendments(_driver)
        return bill

    def _extract_basic_details(self, bill: BillDetail, _driver: BrowserDriver) -> BillDetail:
        """Extract basic bill information"""
        # Last Action
        last_action = self._get_cell_text(_driver, "cellLastAction")
        bill.last_action_dt = re.compile(r'\d{2}/\d{2}/\d{4}').match(last_action).group() if last_action else None

        # Caption Version & Text
        bill.status = self._get_cell_text(_driver, "cellCaptionVersion")
        bill.caption = self._get_cell_text(_driver, "cellCaptionText")
        return bill

    def _extract_action_history(self, bill: BillDetail, _driver: BrowserDriver) -> BillDetail:
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

    def _get_cell_text(self, _driver: BrowserDriver, cell_id: str) -> Optional[str]:
        """Helper method to safely get cell text"""
        try:
            return _driver.find_element(By.ID, cell_id).text.strip()
        except NoSuchElementException:
            return None

    def _extract_amendments(self, bill: BillDetail, _driver: BrowserDriver) -> BillDetail:
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
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 8:
                        links = cells[7].find_elements(By.TAG_NAME, "a")
                        html_link = next((link.get_attribute("href") for link in links
                                          if "html" in link.get_attribute("href").lower()), None)
                        pdf_link = next((link.get_attribute("href") for link in links
                                         if "pdf" in link.get_attribute("href").lower()), None)

                        amendment = Amendment(
                            reading=cells[0].text.strip(),
                            number=cells[1].text.strip(),
                            author=cells[2].text.strip(),
                            coauthors=cells[3].text.strip() if cells[3].text.strip() else None,
                            amendment_type=cells[4].text.strip(),
                            action=cells[5].text.strip(),
                            action_date=cells[6].text.strip(),
                            html_link=html_link,
                            pdf_link=pdf_link
                        )
                        amendments.append(amendment)
                except (NoSuchElementException, IndexError) as e:
                    continue

            bill.amendments = amendments
        except Exception as e:
            bill.amendments = []
        return bill

    def _extract_bill_stages(self, _driver: BrowserDriver) -> List[BillStage]:
        """Extract all bill stage versions and their associated documents"""
        stages = []

        # Find all rows except header
        rows = _driver.find_elements(By.CSS_SELECTOR, "tr:not(:first-child)")

        for row in rows:
            # Skip empty rows
            if not row.text.strip():
                continue

            # Extract version name (first column)
            version = row.find_element(By.CSS_SELECTOR, "td:first-child").text.strip()

            # Get links from second column
            links = row.find_elements(By.CSS_SELECTOR, "td:nth-child(2) a")

            if not links:
                continue

            # Extract document links
            pdf_link = ""
            html_link = ""
            doc_link = ""

            for link in links:
                href = link.get_attribute("href")
                if href.endswith(".pdf"):
                    pdf_link = href
                elif href.endswith(".htm"):
                    html_link = href
                elif href.endswith(".docx"):
                    doc_link = href

            # Get optional documents from remaining columns
            fiscal_note = self._get_link_if_exists(row, 3)
            analysis = self._get_link_if_exists(row, 4)
            witness_list = self._get_link_if_exists(row, 5)
            summary = self._get_link_if_exists(row, 6)

            stage = BillStage(
                version=version,
                pdf=pdf_link,
                txt=html_link,
                word_doc=doc_link,
                fiscal_note=fiscal_note,
                analysis=analysis,
                witness_list=witness_list,
                summary_of_action=summary
            )

            stages.append(stage)

        return stages

    def _get_link_if_exists(self, row: WebElement, col_index: int) -> Optional[str]:
        """Helper to safely get href from cell if link exists"""
        try:
            link = row.find_element(By.CSS_SELECTOR, f"td:nth-child({col_index}) a")
            return link.get_attribute("href")
        except NoSuchElementException:
            return None




class BillListInterface(InterfaceBase):

    def __init__(self):
        super().__init__()
        super()._builder.build()

    @classmethod
    def _navigate_to_bill_page(cls, _chamber: ChamberTuple):
        _driver = super()._builder.DRIVER
        _wait = super()._builder.WAIT
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
    def _get_bill_links(cls):
        _driver = super()._builder.DRIVER
        _wait = super()._builder.WAIT
        _wait.until(
            lambda _driver: _driver.execute_script('return document.readyState') == 'complete'
        )
        bill_tables = _driver.find_elements(By.TAG_NAME, "table")
        return [link for table in bill_tables
                if (link := cls._extract_bill_link(table))]

    @classmethod
    def create_bill_list(cls, chamber: ChamberTuple) -> Dict[str, BillDetail]:
        _driver = super()._builder.DRIVER
        _wait = super()._builder.WAIT
        cls._navigate_to_bill_page(_chamber=chamber)
        bill_links = cls._get_bill_links()
        bills = {}
        for bill in bill_links:
            _detail = BillDetail(
                bill_number=bill[0],
                bill_url=bill[1]
            )
            bills[_detail.bill_number] = _detail
        return bills

    @staticmethod
    def generate_bills(bills: Dict[str, BillDetail]) -> Dict[str, BillDetail]:
        for bill in bills:
            bills[bill] = BillDetailInterface.fetch_bill_details(bills[bill])
        return bills