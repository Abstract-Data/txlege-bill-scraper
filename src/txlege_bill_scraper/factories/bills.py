# factories/bill_factory.py
from typing import List
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from src.txlege_bill_scraper.models.bills import BillDetail, BillStage, Amendment
from src.txlege_bill_scraper.types import BrowserDriver
from src.txlege_bill_scraper.types.bills import BillDetailProtocol, BillStageProtocol, AmendmentProtocol

def create_bill_detail(bill_number: str, bill_url: str) -> BillDetailProtocol:
    return BillDetail(bill_number=bill_number, bill_url=bill_url)

def create_bill_stages(self, _driver: BrowserDriver) -> List[BillStage]:
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

def create_amendment(self, row: WebElement) -> AmendmentProtocol:
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) >= 8:
        links = cells[7].find_elements(By.TAG_NAME, "a")
        html_link = next((link.get_attribute("href") for link in links
                            if "html" in link.get_attribute("href").lower()), None)
        pdf_link = next((link.get_attribute("href") for link in links
                            if "pdf" in link.get_attribute("href").lower()), None)

        return Amendment(
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
