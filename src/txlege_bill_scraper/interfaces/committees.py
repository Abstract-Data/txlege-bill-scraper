from __future__ import annotations

from typing import List, Tuple
from urllib.parse import parse_qs, urlparse

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# from txlege_bill_scraper.protocols import ChamberTuple, HOUSE
from txlege_bill_scraper.build_logger import LogFireLogger

from . import InterfaceBase


class CommitteeInterface(InterfaceBase):
    @classmethod
    @LogFireLogger.logfire_method_decorator(
        "CommitteeInterface._navigate_to_committee_page"
    )
    def navigate_to_page(cls, *args, **kwargs):
        with super().driver_and_wait() as (D_, W_):
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, "Committee Membership")))
            D_.find_element(By.LINK_TEXT, "Committee Membership").click()

    @classmethod
    def _get_committee_list(cls) -> List[Tuple[str, str]]:
        with super().driver_and_wait() as (D_, W_):
            try:
                W_.until(EC.element_to_be_clickable((By.ID, "CmteList")))
            except NoSuchElementException:
                raise Exception("No committee list found")

            _list_of_committees = D_.find_elements(By.ID, "CmteList")
        return [(x.text, x.get_attribute("href")) for x in _list_of_committees]

    @classmethod
    def _get_committee_details(cls, committee: Tuple[str, str]):
        with super().driver_and_wait() as (D_, W_):
            D_.get(committee[1])
            content_div = W_.until(EC.presence_of_element_located((By.ID, "content")))
            _committee_name = committee[0]

            committee_info = {"committee": committee[0], "chamber": cls.chamber.full}
            committee_table = content_div.find_element(By.TAG_NAME, "table")
            rows = committee_table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) == 2:  # Only process rows with two cells
                    key = tuple(cells[0].text.split(":"))
                    value = tuple(cells[1].text.split(":"))
                    if len(value) == 2:
                        committee_info[value[0].strip()] = value[1].strip()
                    if len(key) == 2:
                        committee_info[key[0].strip()] = key[1].strip()

            try:
                members_table = content_div.find_elements(By.TAG_NAME, "table")[
                    1
                ]  # Second table for members
            except IndexError:
                return committee_info

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
            committee_info["members"] = members_info
            return committee_info

    @classmethod
    @LogFireLogger.logfire_method_decorator("CommitteeInterface.create")
    def create(cls):
        cls.navigate_to_page()
        _committees = cls._get_committee_list()
        _details = list(map(lambda x: cls._get_committee_details(x), _committees))
        cls.committees = {x["committee"]: x for x in _details}

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
