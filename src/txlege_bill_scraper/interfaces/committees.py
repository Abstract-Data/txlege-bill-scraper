from __future__ import annotations

from typing import List, Dict, Tuple, Self
from urllib.parse import parse_qs, urlparse
import re

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import inject

from src.txlege_bill_scraper.bases import InterfaceBase, BrowserDriver, BrowserWait
from src.txlege_bill_scraper.protocols import ChamberTuple, HOUSE
from src.txlege_bill_scraper.build_logger import LogFireLogger


logfire_context = LogFireLogger.logfire_context

class CommitteeInterface(InterfaceBase):

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _navigate_to_committee_page(
            cls,
            _driver: BrowserDriver,
            _wait: BrowserWait):

        with logfire_context(f"CommitteeInterface._navigate_to_committee_page({cls.chamber.full})") as ctx:
            ctx.set_attribute("chamber", cls.chamber.full)
            ctx.set_attribute("used_url", "https://capitol.texas.gov/Home.aspx")

            _driver.get("https://capitol.texas.gov/Home.aspx")
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{cls.chamber.full}"))).click()
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"Committee Membership")))
            _driver.find_element(By.LINK_TEXT, "Committee Membership").click()

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _get_committee_list(cls, _driver: BrowserDriver, _wait: BrowserWait) -> List[Tuple[str, str]]:
        try:
            _wait.until(EC.element_to_be_clickable((By.ID, "CmteList")))
        except NoSuchElementException:
            raise Exception("No committee list found")

        _list_of_committees = _driver.find_elements(By.ID, "CmteList")
        return [(x.text, x.get_attribute("href")) for x in _list_of_committees]

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _get_committee_details(cls, committee: Tuple[str, str], _driver: BrowserDriver, _wait: BrowserWait):
            _driver.get(committee[1])
            content_div = _wait.until(EC.presence_of_element_located((By.ID, "content")))
            _committee_name = committee[0]
            # _room_number = re.search(r"\((\w\d{1,3})\)$", _committee_name)
            # if _room_number:
            #     _room_number = _room_number.group(1)

            committee_info = {'committee': committee[0], 'chamber': cls.chamber.full}
            committee_table = content_div.find_element(By.TAG_NAME, "table")
            rows = committee_table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:  # Only process rows with two cells
                    key = tuple(cells[0].text.split(':'))
                    value = tuple(cells[1].text.split(':'))
                    if len(value) == 2:
                        committee_info[value[0].strip()] = value[1].strip()
                    if len(key) == 2:
                        committee_info[key[0].strip()] = key[1].strip()

            # Capture member information from the second table
            members_info = []
            members_table = content_div.find_elements(By.TAG_NAME, "table")[1]  # Second table for members
            member_rows = members_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row

            for member_row in member_rows:
                cells = member_row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    position = (cells[0].text
                                .strip()
                                .replace(":", "")
                                .replace('Members', '')
                                .strip())
                    name_link = cells[1].find_element(By.TAG_NAME, "a")
                    name = name_link.text
                    link = name_link.get_attribute("href")
                    members_info.append({
                        "position": position if position else "Member",
                        "name": name,
                        "id": parse_qs(urlparse(link).query)["LegCode"][0]
                    })
            committee_info["members"] = members_info
            return committee_info

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def create(cls, _driver: BrowserDriver, _wait: BrowserWait):
        cls._navigate_to_committee_page()
        cls._select_legislative_session()
        _committees = cls._get_committee_list()
        _details = list(map(lambda x: cls._get_committee_details(x), _committees))
        cls.committees = {x['committee']: x for x in _details}


            # committee_page = _driver.find_element(By.ID, "content")
            # cls.committees[cls.committees.index(committee)] = (committee[0], committee_page.text)


    # @staticmethod
    # def _extract_committee_link(table_element: WebElement) -> Tuple[str, str] | None:
    #     """Extract committee name and URL from table element"""
    #     try:
    #         link = table_element.find_element(
    #             By.CSS_SELECTOR,
    #             "tr:first-child td:first-child a"
    #         )
    #         return link.text.strip(), link.get_attribute("href")
    #     except NoSuchElementException:
    #         return None
    #
    # @classmethod
    # @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    # def build_committee_list(
    #         cls,
    #         _chamber: ChamberTuple,
    #         _driver: BrowserDriver,
    #         _wait: BrowserWait) -> List[Tuple[str, str]]:
    #
    #     cls._navigate_to_committee_page(_chamber, _driver, _wait)
    #
    #     committee_table = _driver.find_element(By.TAG_NAME, "table")
    #     committee_rows = committee_table.find_elements(By.TAG_NAME, "tr")
    #
    #     return [
    #         cls._extract_committee_link(row)
    #         for row in committee_rows
    #         if (link := cls._extract_committee_link(row)) is not None
    #     ]

# CommitteeInterface.session = 88
# CommitteeInterface.chamber = HOUSE
# details = CommitteeInterface.create()
