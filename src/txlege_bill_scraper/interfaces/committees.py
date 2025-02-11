from __future__ import annotations

from typing import List, Tuple, Dict, Any, Generator
from urllib.parse import parse_qs, urlparse
from icecream import ic

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# from txlege_bill_scraper.protocols import ChamberTuple, HOUSE
from txlege_bill_scraper.build_logger import LogFireLogger

from txlege_bill_scraper.bases import InterfaceBase


class CommitteeInterface(InterfaceBase):
    @classmethod
    @LogFireLogger.logfire_method_decorator(
        "CommitteeInterface._navigate_to_committee_page"
    )
    def navigate_to_page(cls, *args, **kwargs):
        with super().driver_and_wait() as (D_, W_):
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, "Committee Membership")))
            D_.find_element(By.LINK_TEXT, "Committee Membership").click()
            W_.until(EC.element_to_be_clickable((By.ID, "content")))

            # Select Appropriate Legislative Session
            _, cls._tlo_session_dropdown_value = super().select_legislative_session(
                identifier="ddlLegislature"
            )
            W_.until(EC.element_to_be_clickable((By.ID, "content")))

    @classmethod
    @LogFireLogger.logfire_method_decorator("CommitteeInterface._get_committee_list")
    def _get_committee_list(cls) -> Dict:
        with super().driver_and_wait() as (D_, W_):
            ic(D_.current_url)
            _has_committee = "Committees" in D_.current_url
            ic(_has_committee)
            try:
                W_.until(EC.presence_of_element_located((By.ID, "ctl00")))
                _committee_element = D_.find_element(By.ID, "ctl00")
                _committee_table = _committee_element.find_elements(By.TAG_NAME, "li")
            except Exception as e:
                raise e

            _list_of_committees = {}
            for _committee in _committee_table:
                _committee_name = _committee.find_element(By.TAG_NAME, "a").text
                _committee_url = _committee.find_element(
                    By.TAG_NAME, "a"
                ).get_attribute("href")
                _list_of_committees[_committee_name] = {
                    "committee_chamber": cls.chamber.full,
                    "committee_name": _committee_name,
                    "committee_url": _committee_url,
                }
            return _list_of_committees

    @classmethod
    def _get_committee_details(cls, committee: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        with super().driver_and_wait() as (D_, W_):
            D_.get(committee["committee_url"])
            content_div = W_.until(EC.presence_of_element_located((By.ID, "content")))

            committee_table = content_div.find_element(By.TAG_NAME, "table")
            rows = committee_table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:  # Only process rows with two cells
                    key = tuple(cells[0].text.split(":"))
                    value = tuple(cells[1].text.split(":"))
                    if len(value) == 2:
                        committee[value[0].strip()] = value[1].strip()
                    if len(key) == 2:
                        committee[key[0].strip()] = key[1].strip()

            try:
                members_table = content_div.find_elements(By.TAG_NAME, "table")[
                    1
                ]  # Second table for members
            except IndexError:
                return committee

            # Capture member information from the second table
            members_info = []
            member_rows = members_table.find_elements(By.TAG_NAME, "tr")[
                1:
            ]  # Skip header row

            for member_row in member_rows:
                cells = member_row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:
                    position = (
                        cells[0]
                        .text.strip()
                        .replace(":", "")
                        .replace("Members", "")
                        .strip()
                    )
                    name_link = cells[1].find_element(By.TAG_NAME, "a")
                    name = name_link.text
                    link = name_link.get_attribute("href")
                    members_info.append(
                        {
                            "position": position if position else "Member",
                            "name": name,
                            "id": parse_qs(urlparse(link).query)["LegCode"][0],
                        }
                    )
            committee["members"] = members_info
            return committee

    @classmethod
    @LogFireLogger.logfire_method_decorator("CommitteeInterface.fetch")
    def fetch(cls) -> Generator[Dict[str, Dict[str, Any]], None, None]:
        cls.navigate_to_page()
        _committees = cls._get_committee_list()
        for committee in _committees:
            yield {committee: cls._get_committee_details(_committees[committee])}
        #     _committees[committee] = cls._get_committee_details(_committees[committee])
        # _details = {x: cls._get_committee_details(_committees[x]) for x in _committees}
        # cls.committees = {x["committee"]: x for x in _details}
        # return _details

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
