# factories/bill_factory.py
from typing import Optional, Dict
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import logfire
import re

from src.txlege_bill_scraper.protocols import ChamberTuple
from src.txlege_bill_scraper.models.bills import BillDetail, BillStage, Amendment, DocumentVersionLink, FiscalImpactStatement
from src.txlege_bill_scraper.models.committees import CommitteeDetails, CommitteeVoteCount, CommitteeBillStatus
from src.txlege_bill_scraper.build_logger import LogFireLogger

logfire_context = LogFireLogger.logfire_context


def _get_cell_text(cell_id: str, _driver) -> Optional[str]:
    """Helper method to safely get cell text.

    :param cell_id: The ID of the cell to retrieve text from.
    :type cell_id: str
    :param _driver: The Selenium WebDriver instance.
    :type _driver: WebDriver
    :return: The text content of the cell, or None if not found.
    :rtype: Optional[str]
    """
    try:
        return _driver.find_element(By.ID, cell_id).text.strip()
    except NoSuchElementException:
        return None

def create_bill_detail(bill_number: str, bill_url: str) -> BillDetail:
    """Create a BillDetail object.

    :param bill_number: The bill number.
    :type bill_number: str
    :param bill_url: The URL of the bill.
    :type bill_url: str
    :return: The created BillDetail object.
    :rtype: BillDetail
    """
    return BillDetail(bill_number=bill_number, bill_url=bill_url)


def extract_basic_details(_bill: BillDetail, _chamber: ChamberTuple, _committees: Dict[str, CommitteeDetails], _driver) -> BillDetail:
    """Extract basic bill information.

    :param bill: The BillDetail object to update.
    :type bill: BillDetail
    :param _driver: The Selenium WebDriver instance.
    :type _driver: WebDriver
    :return: The updated BillDetail object.
    :rtype: BillDetail
    """

    def _get_cell_content(cell_id: str) -> Optional[str]:
        try:
            cell = _driver.find_element(By.ID, cell_id)
            # Check for nested link
            links = cell.find_elements(By.TAG_NAME, "a")
            if links:
                return {
                    'text': cell.text.strip(),
                    'url': links[0].get_attribute('href')
                }
            return cell.text.strip()
        except NoSuchElementException:
            return None
        
    def _parse_committee_vote(vote_text: str) -> dict:
        """Parse committee vote string into components."""
        vote_dict = {}
        if not vote_text:
            return vote_dict
            
        # Extract vote counts using regex
        vote_pattern = r'Ayes=(\d+)\s*Nays=(\d+)\s*Present Not Voting=(\d+)\s*Absent=(\d+)'
        if match := re.match(vote_pattern, vote_text):
            vote_dict = CommitteeVoteCount(**{
                'committee_bill_vote_id': _bill.bill_number,
                'ayes': int(match.group(1)),
                'nays': int(match.group(2)),
                'present_not_voting': int(match.group(3)),
                'absent': int(match.group(4))
            })
        return vote_dict
    
    def _get_subjects(driver) -> list[str]:
        """Extract and split subjects from cell."""
        try:
            subjects_cell = driver.find_element(By.ID, "cellSubjects")
            # Get all text nodes separated by <br>
            subject_text = subjects_cell.get_attribute('innerHTML')
            # Split on <br> or <br/> and clean
            subjects = [
                subj.strip() 
                for subj in subject_text.split('<br/>') 
                if subj.strip()
            ]
            return subjects
        except NoSuchElementException:
            return []
    
    _bill.last_action_dt = re.compile(r'\d{2}/\d{2}/\d{4}').match(_get_cell_content('cellLastAction')).group() if _get_cell_content('cellLastAction') else None
    _bill.caption_version = _get_cell_content('cellCaptionVersion')
    _bill.caption_text = _get_cell_content('cellCaptionText')
    _bill.author = _get_cell_content('cellAuthors')
    _bill.sponsor = _get_cell_content('cellSponsors')
    _bill.subjects = _get_subjects('cellSubjects')
    _bill.companion = _get_cell_content('cellCompanions')
    
    if _house_committee_exists := _get_cell_content('cellComm1Committee'):
        _check_house_committee_ = CommitteeDetails(name=_house_committee_exists, chamber='House')
        if _check_house_committee_.__hash__() in _committees:
            _house_committee = _committees[_check_house_committee_.__hash__()]
        else:
            _house_committee = _check_house_committee_
    
        _house_status = CommitteeBillStatus(
            committee_bill_num=_bill.bill_number,
            status=_get_cell_content('cellComm1CommitteeStatus'),
            vote=_parse_committee_vote('cellComm1CommitteeVote')
        )
        _bill.house_committee = _house_committee
        _bill.house_committee_status = _house_status

    if _senate_committee_exists := _get_cell_content('cellComm2Committee'):
        _check_senate_committee_ = CommitteeDetails(name=_senate_committee_exists, chamber='Senate')
        if _check_senate_committee_.__hash__() in _committees:
            _senate_committee = _committees[_check_senate_committee_.__hash__()]
        else:
            _senate_committee = _check_senate_committee_

        _senate_status = CommitteeBillStatus(
            committee_bill_num=_bill.bill_number,
            status=_get_cell_content('cellComm2CommitteeStatus'),
            vote=_parse_committee_vote('cellComm2CommitteeVote')
        )
        _bill.senate_committee = _senate_committee
        _bill.senate_committee_status = _senate_status

    if _house_committee_exists:
        _house_committee.committee_bills.append(_bill)
        _committees[_house_committee.__hash__()] = _house_committee
    if _senate_committee_exists:
        _senate_committee.committee_bills.append(_bill)
        _committees[_senate_committee.__hash__()] = _senate_committee
    return _bill,

def extract_action_history(bill: BillDetail, _driver) -> BillDetail:
    """Extract bill action history.

    :param bill: The BillDetail object to update.
    :type bill: BillDetail
    :param _driver: The Selenium WebDriver instance.
    :type _driver: WebDriver
    :return: The updated BillDetail object with action history.
    :rtype: BillDetail
    """
    try:
        action_rows = _driver.find_elements(By.CSS_SELECTOR, "#usrBillInfoActions_tblActions + table tr:not(:first-child)")

        actions = []
        for row in action_rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 6:
                description_link = cells[1].find_elements(By.TAG_NAME, "a")
                action = {
                    'Chamber': cells[0].text.strip(),
                    'Description': cells[1].text.strip(),
                    'Comment': cells[2].text.strip(),
                    'Date': cells[3].text.strip(),
                    'Time': cells[4].text.strip(),
                    'Journal_Page': cells[5].text.strip(),
                    'URL': description_link[0].get_attribute('href') if description_link else None
                }
                actions.append(action)

        bill.action_list = actions
    except NoSuchElementException:
        bill.action_list = None
    return bill



def create_bill_stages(bill: BillDetail, _driver, _wait) -> BillDetail:
    """Create bill stages and extract related documents.

    :param bill: The BillDetail object to update.
    :type bill: BillDetail
    :param _driver: The Selenium WebDriver instance.
    :type _driver: WebDriver
    :param _wait: The WebDriverWait instance.
    :type _wait: WebDriverWait
    :return: The updated BillDetail object with stages and documents.
    :rtype: BillDetail
    """
    def get_bill_documents() -> BillDetail:
        """Retrieve bill documents including versions, additional documents, and fiscal impacts.

        :return: The updated BillDetail object with documents.
        :rtype: BillDetail
        """
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
        """Extract version table data and update bill stages.

        :return: The updated BillDetail object with version table data.
        :rtype: BillDetail
        """
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
        """Extract additional documents related to the bill.

        :return: The updated BillDetail object with additional documents, or None if not found.
        :rtype: None | BillDetail
        """
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
        """Extract fiscal impact statements related to the bill.

        :return: The updated BillDetail object with fiscal impacts, or None if not found.
        :rtype: None | BillDetail
        """
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
                    if impact_link_type.text.strip():
                        # impact_links[impact_link_type.text] = DocumentVersionLink(
                        #     **{determine_doc_type(impact_link): impact_link}
                        # )
                        bill.stages[version].fiscal_impact_statements = (
                            FiscalImpactStatement(
                                version=version, 
                                released_by=impact_link_type.text,
                                documents={determine_doc_type(impact_link): impact_link}
                            )
                        )
                    return
        except NoSuchElementException:
            return

    def get_links_from_cell(cell) -> DocumentVersionLink:
        """Extract all links from a table cell with their types.

        :param cell: The table cell element.
        :type cell: WebElement
        :return: The DocumentVersionLink object containing extracted links.
        :rtype: DocumentVersionLink
        """
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
        """Determine document type from URL.

        :param url: The URL of the document.
        :type url: str
        :return: The document type (pdf, word, html, or unknown).
        :rtype: str
        """
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


def extract_amendments(bill: BillDetail, _driver: "BrowserDriver") -> BillDetail:
    """Extract all amendments and their associated documents.

    :param bill: The BillDetail object to update.
    :type bill: BillDetail
    :param _driver: The Selenium WebDriver instance.
    :type _driver: BrowserDriver
    :return: The updated BillDetail object with amendments.
    :rtype: BillDetail
    """
    amendments_url = bill.bill_url.replace("Text.aspx", "Amendments.aspx")
    _driver.get(amendments_url)
    try:
        # Check if any amendments exist
        amendment_count = _driver.find_element(By.ID, "usrBillInfoAmendments_lblAmendments").text
        if "0" in amendment_count:
            bill.amendments = []
            return bill

        amendment_table = _driver.find_element(By.CSS_SELECTOR, "table[bordercolor='#d0d0d0']")
        if not amendment_table:
            bill.amendments = []
            return bill

        amendment_rows = amendment_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
        if not amendment_rows:
            bill.amendments = []
            return bill

        for row in amendment_rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                _amendment_dict = {
                    'reading': cells[0].text.strip(),
                    'number': cells[1].text.strip(),
                    'author': cells[2].text.strip(),
                    'coauthors': cells[3].text.strip() if cells[3].text.strip() else None,
                    'amendment_type': cells[4].text.strip(),
                    'action': cells[5].text.strip(),
                    'action_date': cells[6].text.strip()
                }
                if len(cells) >= 8:
                    links = cells[7].find_elements(By.TAG_NAME, "a")
                    _amendment_dict["html_link"] = next((link.get_attribute("href") for link in links
                                                         if "html" in link.get_attribute("href").lower()), None)
                    _amendment_dict["pdf_link"] = next((link.get_attribute("href") for link in links
                                                        if "pdf" in link.get_attribute("href").lower()), None)
                amendment = Amendment(**_amendment_dict)
                bill.amendments.append(amendment)
            except (NoSuchElementException, IndexError) as e:
                continue

    except Exception as e:
        pass
    return bill
