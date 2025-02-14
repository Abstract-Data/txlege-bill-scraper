import functools
from typing import Optional, List, Dict, Any
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import string
from urllib.parse import parse_qs, urlparse

from urllib.parse import urljoin
import httpx
import asyncio

from driver import BuildWebDriver, WebDriver
from interfaces.link_builders.bases import LegislativeSessionLinkBuilder

# driver = BuildWebDriver()
# driver.build()
# DRIVER_AND_WAIT = driver.driver_and_wait(_driver=BuildWebDriver.DRIVER, _wait=BuildWebDriver.WAIT)
base_url = 'https://capitol.texas.gov'
test_url = "https://capitol.texas.gov/BillLookup/AmendmentCoauthors.aspx?LegSess=87R&Bill=HB2&AmndChamber=H&AmndRdg=2&AmndNbr=++++3"
member_test = {
    'name': 'test_name',
    'member_url': test_url
}
response = httpx.get(test_url)
soup = BeautifulSoup(response.text, 'html.parser')
tables = soup.find_all("table", id="tblCoauthors")[0]
rows = tables.find(id='cellCoauthors')
content = [x.strip() for x in rows.text.split('|')]
for row in rows:
    cells = row.find_all("td")
    if len(cells) >= 3:
        print(cells[1].text.strip())
# with DRIVER_AND_WAIT as (D_, W_):
#     try:
#         D_.get("https://capitol.texas.gov/BillLookup/History.aspx?LegSess=871&Bill=HB1")
#         bill_info = {}
#         base_url = "https://capitol.texas.gov/BillLookup/"
#
#         # Last Action Date
#         last_action = W_.until(EC.presence_of_element_located((By.ID, "cellLastAction")))
#         date_match = re.compile(r'\d{2}/\d{2}/\d{4}').search(last_action.text)
#         bill_info['last_action_dt'] = date_match.group() if date_match else None
#
#         # Caption Version
#         caption_version = D_.find_element(By.ID, "cellCaptionVersion")
#         bill_info['caption_version'] = caption_version.text.strip()
#
#         # Caption Text
#         caption_text = D_.find_element(By.ID, "cellCaptionText")
#         bill_info['caption_text'] = caption_text.text.strip()
#
#         # Author
#         try:
#             authors = D_.find_element(By.ID, "cellAuthors")
#             bill_info['author'] = authors.text.strip()
#         except:
#             bill_info['author'] = None
#
#         # Sponsor
#         try:
#             sponsors = D_.find_element(By.ID, "cellSponsors")
#             bill_info['sponsor'] = sponsors.text.strip()
#         except:
#             bill_info['sponsor'] = None
#
#         # Subjects
#         try:
#             subjects = D_.find_element(By.ID, "cellSubjects")
#             bill_info['subjects'] = [s.strip() for s in subjects.text.split('\n') if s.strip()]
#         except:
#             bill_info['subjects'] = []
#
#         # Companion
#         try:
#             companions = D_.find_element(By.ID, "cellCompanions")
#             companion_link = companions.find_element(By.TAG_NAME, "a")
#             href = companion_link.get_attribute("href")
#             bill_info['companion'] = {
#                 'companion_url': href,
#                 'companion_number': companion_link.get_attribute("innerText").replace(" ", "").strip()
#             }
#         except:
#             bill_info['companion'] = None
#
#         # Committee information
#         committee_info = {}
#         try:
#
#             # House Committee
#             committee_cell = D_.find_element(By.ID, "cellComm1Committee")
#             committee_link = committee_cell.find_element(By.TAG_NAME, "a")
#             committee_info['name'] = committee_link.text.strip()
#             committee_info['url'] = committee_link.get_attribute("href")
#
#             # Committee Status
#             status_cell = D_.find_element(By.ID, "cellComm1CommitteeStatus")
#             committee_info['status'] = status_cell.text.strip()
#
#             # Committee Vote
#             try:
#                 vote_cell = D_.find_element(By.ID, "cellComm1CommitteeVote")
#                 vote_text = vote_cell.text.strip()
#
#                 # Parse vote counts
#                 ayes = re.search(r'Ayes=(\d+)', vote_text)
#                 nays = re.search(r'Nays=(\d+)', vote_text)
#                 pnv = re.search(r'Present Not Voting=(\d+)', vote_text)
#                 absent = re.search(r'Absent=(\d+)', vote_text)
#
#                 committee_info['votes'] = {
#                     'ayes': int(ayes.group(1)) if ayes else 0,
#                     'nays': int(nays.group(1)) if nays else 0,
#                     'present_not_voting': int(pnv.group(1)) if pnv else 0,
#                     'absent': int(absent.group(1)) if absent else 0
#                 }
#             except:
#                 committee_info['votes'] = None
#
#             bill_info['committee'] = committee_info
#
#         except:
#             bill_info['committee'] = None
#
#         try:
#             table = W_.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[rules='rows']")))
#             rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
#
#             actions = []
#             for row in rows:
#                 cells = row.find_elements(By.TAG_NAME, "td")
#                 if len(cells) >= 6:
#                     # Check for link in description cell
#                     try:
#                         action_link = cells[1].find_element(By.TAG_NAME, "a")
#                         action_url = action_link.get_attribute("href")
#                     except:
#                         action_url = None
#
#                     action = {
#                         'chamber': cells[0].text.strip(),
#                         'description': cells[1].text.strip(),
#                         'comment': cells[2].text.strip(),
#                         'date': cells[3].text.strip(),
#                         'time': cells[4].text.strip(),
#                         'journal_page': cells[5].text.strip(),
#                         'action_url': action_url
#                     }
#                     actions.append(action)
#         except:
#             actions = []
#         bill_info['actions'] = actions
#     except Exception as e:
#         print(e)
    # _get_cell_content = functools.partial(get_cell_content, _driver=D_)
    # _bill = {}
    # _bill['last_action_dt'] = (
    #     re
    #     .compile(r'\d{2}/\d{2}/\d{4}')
    #     .match(
    #         _get_cell_content('cellLastAction')
    #     )
    #     .group() if _get_cell_content('cellLastAction') else None
    # )
    # _bill['caption_version'] = _get_cell_content('cellCaptionVersion')
    # _bill['caption_text'] = _get_cell_content('cellCaptionText')
    # _bill['author'] = _get_cell_content('cellAuthors')
    # _bill['sponsor'] = _get_cell_content('cellSponsors')
    # _bill['subjects'] = _get_subjects(D_)
    # _bill['companion'] = _get_cell_content('cellCompanions')