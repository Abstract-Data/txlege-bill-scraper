from __future__ import annotations

from typing import List, Tuple, Dict, Any, Generator
from urllib.parse import parse_qs, urlparse, urljoin

import logfire
from icecream import ic
from bs4 import BeautifulSoup

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from . import LegislativeSessionLinkBuilder
from models.committees import CommitteeDetails
from protocols import TYPE_PREFIXES, ChamberTuple

class CommitteeInterface(LegislativeSessionLinkBuilder):

    @classmethod
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
    def get_links(cls) -> Dict[str, Dict[str, str]]:
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

            soup = BeautifulSoup(D_.page_source, "html.parser")
            _container = soup.find("div", {"id": "content"})
            _committee_table = _container.find_all("li")
            _committee_url_pfx = urljoin(cls._base_url, TYPE_PREFIXES.COMMITTEES)
            _list_of_committees = {}
            for _committee in _committee_table:
                _committee_link = _committee.find("a")
                _committee_name = _committee_link.text.strip()
                _committee_url = _committee_link.get("href")
                _committee_id = parse_qs(urlparse(_committee_url).query)["CmteCode"][0]
                _list_of_committees[_committee_id] = CommitteeDetails(
                    id=_committee_id,
                    committee_id=f"{cls.lege_session_id}-{_committee_id}",
                    committee_name=_committee_name,
                    committee_chamber= cls.chamber.full,
                    committee_url= urljoin(_committee_url_pfx, _committee_url),
                )
            return _list_of_committees
