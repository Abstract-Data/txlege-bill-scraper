# factories/bill_factory.py
from __future__ import annotations
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from pydantic.alias_generators import to_snake
import logfire

from src.txlege_bill_scraper.models.bills import BillDetail, BillStage, Amendment, DocumentVersionLink
from src.txlege_bill_scraper.build_logger import LogFireLogger

logfire_context = LogFireLogger.logfire_context

def create_bill_detail(bill_number: str, bill_url: str) -> BillDetail:
    return BillDetail(bill_number=bill_number, bill_url=bill_url)


def create_bill_stages(bill: BillDetail, _driver, _wait) -> BillDetail:

    def get_bill_documents() -> BillDetail:
        try:

            _driver.get(bill.bill_url.replace("History", "Text"))
            # Wait for the main table to load
            _wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr:not(:first-child)")))

            # Get main version table data
            get_versions_table()

            # Get additional documents
            get_additional_documents()

            # Get fiscal impact statements
            get_fiscal_impacts()

        except Exception:
            logfire.error(f"Error getting bill documents for {bill.bill_number}")
        return bill

    def get_versions_table() -> BillDetail:
        rows = _driver.find_elements(By.CSS_SELECTOR, "tr:not(:first-child)")

        for row in rows:
            # Skip rows that don't have enough cells
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 6:
                continue
            __stage_name = cells[0].text.strip()
            _stage_dict[__stage_name] = BillStage(**{
                'version': __stage_name,
                'bill': get_links_from_cell(cells[1]),
                'fiscal_note': get_links_from_cell(cells[2]),
                'analysis': get_links_from_cell(cells[3]),
                'witness_list': get_links_from_cell(cells[4]),
                'committee_summary': get_links_from_cell(cells[5])
            })
            _stage_dict.pop('Additional Documents:', None)

            bill.stages.update(_stage_dict)
        return bill

    def get_additional_documents() -> None | BillDetail:
        if not _stage_dict:
            return None
        try:
            additional_docs_table = _driver.find_element(By.ID, "tblAddlDocs")
            docs = {}

            # Find all links in the additional documents table
            links = additional_docs_table.find_elements(By.TAG_NAME, "a")
            for link in links:
                text = link.text.strip()
                if text:
                    docs[text] = {
                        'txt': link.get_attribute('href')
                    }

            bill.additional_documents = {k: DocumentVersionLink(**v) for k, v in docs.items() if v}
            return
        except NoSuchElementException:
            return None

    def get_fiscal_impacts() -> None | BillDetail:
        try:
            # Find the fiscal impacts section by its text
            fiscal_table = _driver.find_elements(By.CSS_SELECTOR, "table")[-1]  # Usually the last table
            rows = fiscal_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    impact_links = {}
                    version = cells[0].text.strip()
                    impact_link_type = cells[1].find_element(By.TAG_NAME, "a")
                    impact_link = impact_link_type.get_attribute('href')
                    impact_links[impact_link_type.text] = DocumentVersionLink(
                        **{determine_doc_type(impact_link): impact_link}
                    )
                    bill.stages[version].fiscal_impact_statements = {impact_link_type.text: impact_links}
                    return
        except NoSuchElementException:
            return

    def get_links_from_cell(cell) -> DocumentVersionLink:
        """Extract all links from a table cell with their types"""
        links = {}
        try:
            for link in cell.find_elements(By.TAG_NAME, "a"):
                href = link.get_attribute('href')
                if href:
                    doc_type = determine_doc_type(href)
                    links[doc_type] = href
        except NoSuchElementException:
            pass

        return DocumentVersionLink(**links) if links else None

    def determine_doc_type(url: str) -> str:
        """Determine document type from URL"""
        if '.pdf' in url.lower():
            return 'pdf'
        elif '.doc' in url.lower() or '.docx' in url.lower():
            return 'word'
        elif '.htm' in url.lower():
            return 'html'
        return 'unknown'

    _stage_dict = {}
    get_bill_documents()
    # if len(_stage_dict) == 0:
    #     logfire.debug("No bill stages found")
    # stage_list = []
    # for k, v in _stage_dict.items():
    #     stage_list.append(v)
    return bill

def create_amendment(_amendment_dict: dict) -> Amendment:
    return Amendment(**_amendment_dict)
