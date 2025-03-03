# from typing import Optional, List, Dict, Any, Generator
# import re
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
#
# from urllib.parse import urljoin
#
# from build_logger import LogFireLogger
# from driver import BuildWebDriver, WebDriver
# from .link_builders.bases import LegislativeSessionLinkBuilder
#
#
# def get_cell_content(cell_id: str, _driver) -> Optional[str]:
#     try:
#         cell = _driver.find_element(By.ID, cell_id)
#         # Check for nested link
#         links = cell.find_elements(By.TAG_NAME, "a")
#         if links:
#             return {
#                 'text': cell.text.strip(),
#                 'url': links[0].get_attribute('href')
#             }
#         return cell.text.strip()
#     except NoSuchElementException:
#         return None
#
#
# def _get_subjects(_driver: WebDriver ) -> list[str]:
#     """Extract and split subjects from cell."""
#     try:
#         subjects_cell = _driver.find_element(By.ID, "cellSubjects")
#         # Get all text nodes separated by <br>
#         subject_text = subjects_cell.get_attribute('innerHTML')
#         # Split on <br> or <br/> and clean
#         subjects = [
#             subj.strip()
#             for subj in subject_text.split('<br/>')
#             if subj.strip()
#         ]
#         return subjects
#     except NoSuchElementException:
#         return []
#
#
#
# class BillDetailInterface(LegislativeSessionLinkBuilder):
#
#     def navigate_to_page(cls, *args, **kwargs) -> None:
#         pass
#
#
#     @classmethod
#     def get_basic_details(cls, bill: Dict[str, Any]) -> Dict[str, Any]:
#         with cls.driver_and_wait() as (D_, W_):
#             D_.get(bill['bill_url'])
#             bill_info = {}
#
#             # Last Action Date
#             last_action = W_.until(EC.presence_of_element_located((By.ID, "cellLastAction")))
#             date_match = re.compile(r'\d{2}/\d{2}/\d{4}').search(last_action.text)
#             bill_info['last_action_dt'] = date_match.group() if date_match else None
#
#             # Caption Version
#             caption_version = D_.find_element(By.ID, "cellCaptionVersion")
#             bill_info['caption_version'] = caption_version.text.strip()
#
#             # Caption Text
#             caption_text = D_.find_element(By.ID, "cellCaptionText")
#             bill_info['caption_text'] = caption_text.text.strip()
#             # Author
#             try:
#                 authors = D_.find_element(By.ID, "cellAuthors")
#                 bill_info['author'] = authors.text.strip()
#             except ValueError:
#                 bill_info['author'] = None
#
#             # Sponsor
#             try:
#                 sponsors = D_.find_element(By.ID, "cellSponsors")
#                 bill_info['sponsor'] = sponsors.text.strip()
#             except ValueError:
#                 bill_info['sponsor'] = None
#
#             # Subjects
#             try:
#                 subjects = D_.find_element(By.ID, "cellSubjects")
#                 bill_info['subjects'] = [s.strip() for s in subjects.text.split('\n') if s.strip()]
#             except ValueError:
#                 bill_info['subjects'] = []
#
#             # Companion
#             try:
#                 companions = D_.find_element(By.ID, "cellCompanions")
#                 companion_link = companions.find_element(By.TAG_NAME, "a")
#                 href = companion_link.get_attribute("href")
#                 bill_info['companion'] = {
#                     'companion_url': href,
#                     'companion_number': companion_link.get_attribute("innerText").replace(" ", "").strip()
#                 }
#             except:
#                 bill_info['companion'] = None
#             bill.update(bill_info)
#         return bill
#
#     @classmethod
#     def _get_committee_information(cls, committee_cell_tag: str = "cellComm1") -> dict:
#         # Committee information
#         committee_info = {}
#         with cls.driver_and_wait() as (D_, W_):
#             try:
#
#                 # House Committee
#                 committee_cell = D_.find_element(By.ID, f"{committee_cell_tag}Committee")
#                 committee_link = committee_cell.find_element(By.TAG_NAME, "a")
#                 committee_info['chamber'] = "House" if committee_cell_tag.startswith("cellComm1") else "Senate"
#                 committee_info['name'] = committee_link.text.strip()
#                 committee_info['url'] = committee_link.get_attribute("href")
#
#                 # Committee Status
#                 status_cell = D_.find_element(By.ID, f"{committee_cell_tag}Status")
#                 committee_info['status'] = status_cell.text.strip()
#
#                 # Committee Vote
#                 try:
#                     vote_cell = D_.find_element(By.ID, f"{committee_cell_tag}Vote")
#                     vote_text = vote_cell.text.strip()
#
#                     # Parse vote counts
#                     ayes = re.search(r'Ayes=(\d+)', vote_text)
#                     nays = re.search(r'Nays=(\d+)', vote_text)
#                     pnv = re.search(r'Present Not Voting=(\d+)', vote_text)
#                     absent = re.search(r'Absent=(\d+)', vote_text)
#
#                     committee_info['votes'] = {
#                         'ayes': int(ayes.group(1)) if ayes else 0,
#                         'nays': int(nays.group(1)) if nays else 0,
#                         'present_not_voting': int(pnv.group(1)) if pnv else 0,
#                         'absent': int(absent.group(1)) if absent else 0
#                     }
#                 except ValueError:
#                     committee_info['votes'] = None
#
#             except ValueError:
#                 committee_info = None
#             return committee_info
#
#     @classmethod
#     def parse_bill_text_table(cls) -> Any:
#         with cls.driver_and_wait() as (D_, W_):
#             versions = []
#             bill_text = D_.current_url.replace("History.aspx", "Text.aspx")
#             D_.get(bill_text)
#             W_.until(EC.presence_of_element_located((By.ID, "Form1")))
#             soup = BeautifulSoup(D_.page_source, 'html.parser')
#             tables = soup.find_all("form")[1]
#             bill_table = tables.find_next("table")
#             rows = bill_table.find_all("tr")[1:]
#             for row in rows:
#                 cells = row.find_all("td")
#                 if len(cells) >= 6:
#                     version_info = {
#                         'version': cells[0].text.strip(),
#                         'bill_docs': [],
#                         'fiscal_note_docs': [],
#                         'analysis_docs': [],
#                         'witness_list_docs': [],
#                         'committee_summary_docs': []
#                     }
#
#                     # Process Bill documents (cell 1)
#                     bill_links = cells[1].find_all("a")
#                     for link in bill_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href)
#                             version_info['bill_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#
#                     # Process Fiscal Note documents (cell 2)
#                     fiscal_links = cells[2].find_all("a")
#                     for link in fiscal_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href)
#                             version_info['fiscal_note_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#
#                     # Process Analysis documents (cell 3)
#                     analysis_links = cells[3].find_all("a")
#                     for link in analysis_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href)
#                             version_info['analysis_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#
#                     # Process Witness List documents (cell 4)
#                     witness_links = cells[4].find_all("a")
#                     for link in witness_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href)
#                             version_info['witness_list_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#
#                     # Process Committee Summary documents (cell 5)
#                     summary_links = cells[5].find_all("a")
#                     for link in summary_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href)
#                             version_info['committee_summary_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#
#                     versions.append(version_info)
#             return versions
#
#     @classmethod
#     def parse_amendments_table(cls):
#         with cls.driver_and_wait() as (D_, W_):
#             amendments = []
#             D_.get(D_.current_url.replace('Text.aspx', 'Amendments.aspx'))
#             W_.until(EC.presence_of_element_located((By.ID, "ctl00")))
#             soup = BeautifulSoup(D_.page_source, 'html.parser')
#             tables = soup.find_all("form")[1]
#             amendments_table = tables.find_next("table")
#             rows = amendments_table.find_all("tr")[1:]
#             for row in rows:
#                 cells = row.find_all("td")
#                 if len(cells) >= 7:
#                     amendment_info = {
#                         'amendment_chamber': cells[0].text.strip().split()[0],
#                         'amendment_reading': cells[0].text.strip().split()[1],
#                         'amendment_number': cells[1].text.strip(),
#                         'amendment_author': cells[2].text.strip(),
#                         'amendment_coauthor': cells[3].text.strip(),
#                         'amendment_type': cells[4].text.strip(),
#                         'amendment_action': cells[5].text.strip(),
#                         'amendment_action_date': cells[6].text.strip(),
#                         'amendment_docs': []
#                     }
#                     # Check for link in description cell
#                     amendment_links = cells[7].find_all("a")
#                     for link in amendment_links:
#                         href = link.get("href")
#                         if href:
#                             doc_type = cls.get_document_type(href.lower())
#                             amendment_info['amendment_docs'].append({
#                                 'url': urljoin(cls._base_url, href),
#                                 'type': doc_type
#                             })
#                     amendments.append(amendment_info)
#             return amendments
#
#     @classmethod
#     @LogFireLogger.logfire_method_decorator("BillDetailInterface.fetch")
#     def fetch(cls, bills: Dict[str, Dict[str, Any]]) -> Generator[Dict[str, Dict[str, Any]], None, None]:
#         for num, bill in bills.items():
#             bill = cls.get_basic_details(bill)
#             house_committee = cls._get_committee_information("cellComm1")
#             senate_committee = cls._get_committee_information("cellComm2")
#             bill['house_committee'] = house_committee
#             bill['senate_committee'] = senate_committee
#             bill['versions'] = cls.parse_bill_text_table()
#             bill['amendments'] = cls.parse_amendments_table()
#             yield {num: bill}
