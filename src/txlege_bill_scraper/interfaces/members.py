from __future__ import annotations

from typing import Any, Dict, List, Generator
from urllib.parse import parse_qs, urlparse
from icecream import ic

import logfire
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from txlege_bill_scraper.build_logger import LogFireLogger

from txlege_bill_scraper.bases import InterfaceBase



class MemberDetailInterface(InterfaceBase):


    @classmethod
    def navigate_to_page(cls, *args, **kwargs) -> Dict[str, Dict]:
        member: Dict[str, Any] | None = kwargs.get("member", None)
        if member is None:
            raise Exception("No member provided")
        with super().driver_and_wait() as (D_, W_):
            D_.get(member["url"])
            W_.until(EC.element_to_be_clickable((By.ID, "content")))

    @classmethod
    def _get_member_details(cls, member: Dict) -> Dict | None:
        #TODO: Build ability to get committee assignments for previous session if on the page.
        with super().driver_and_wait() as (D_, W_):
            _remove_information_pfx = f"Information for {cls.chamber.member_pfx}."
            _member_header = D_.find_element(By.ID, "usrHeader_lblPageTitle")
            _member_header_text = _member_header.text.replace(
                _remove_information_pfx, ""
            ).strip()
            member["last_name"] = member["name"]
            member["first_name"] = _member_header_text.replace(
                member["last_name"], ""
            ).strip()
            if "first_name" in member and "last_name" in member:
                del member["name"]

            try:
                _contact_info = D_.find_element(By.ID, "contactInfo")
                with super().get_text_by_label_context(_contact_info) as get_:
                    member["district"] = get_("lblDistrict")
                    member["capitol_office"] = get_("lblCapitolOffice")
                    member["capitol_address1"] = get_("lblCapitolAddress1")
                    member["capitol_address2"] = get_("lblCapitolAddress2")
                    member["capitol_phone"] = get_("lblCapitolPhone")
                    member["district_address1"] = get_("lblDistrictAddress1")
                    member["district_address2"] = get_("lblDistrictAddress2")
                    member["district_phone"] = get_("lblDistrictPhone")
            except NoSuchElementException:
                pass

            try:
                _legislative_info = D_.find_element(By.ID, "legislativeInformation")
                _legislative_links = _legislative_info.find_elements(By.TAG_NAME, "a")
                get_url_ = lambda txt: next(
                    (
                        x.get_attribute("href")
                        for x in _legislative_links
                        if txt in x.text
                    ),
                    None,
                )
                member["bills_authored_url"] = get_url_("Bills Authored")
                member["bills_sponsored_url"] = get_url_("Bills Sponsored")
                member["bills_coauthored_url"] = get_url_("Bills Coauthored")
                member["bills_cosponsored_url"] = get_url_("Bills Cosponsored")
                member["amendments_authored_url"] = get_url_("Amendments Authored")
            except NoSuchElementException:
                pass
            member = cls._get_member_bills(member)
            return member

    @classmethod
    def _get_member_bills(cls, member: Dict) -> Dict | None:
        with super().driver_and_wait() as (D_, W_):
            _urls = {k: v for k, v in member.items() if k.endswith("_url")}
            W_ = WebDriverWait(D_, 2)
            bill_type_list = {}
            for _type, url in _urls.items():
                D_.get(url)
                try:
                    W_.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    _bill_table = D_.find_elements(By.TAG_NAME, "table")
                    bill_type_list[_type.replace("_url", "")] = []
                    for _bill in _bill_table:
                        _bill_url = _bill.find_element(By.TAG_NAME, "a").get_attribute(
                            "href"
                        )
                        _session = parse_qs(urlparse(_bill_url).query)["LegSess"][0]
                        _bill_num = parse_qs(urlparse(_bill_url).query)["Bill"][0]
                        bill_type_list[_type.replace("_url", "")].append(
                            f"{_session}_{_bill_num}"
                        )
                except Exception:
                    pass
            member.update(bill_type_list)
        return member

    @classmethod
    def fetch(cls, member: Dict) -> Dict | None:
        cls.navigate_to_page(member=member)
        return cls._get_member_details(member=member)


class MemberListInterface(InterfaceBase):


    @classmethod
    @LogFireLogger.logfire_method_decorator(
        "MemberListInterface._navigate_to_member_list"
    )
    def navigate_to_page(cls):
        with super().driver_and_wait() as (D_, W_):
            logfire.debug(f"Navigating to {cls.chamber.full} member page")
            W_.until(
                EC.element_to_be_clickable(
                    (By.LINK_TEXT, f"{cls.chamber.full} Members")
                )
            ).click()
            W_.until(EC.element_to_be_clickable((By.ID, "content"))).is_displayed()
            _, cls._tlo_session_dropdown_value = super().select_legislative_session(
                identifier="ddlLegislature"
            )

    @classmethod
    def _get_member_list(cls) -> List[Dict]:
        with super().driver_and_wait() as (D_, W_):
            try:
                W_.until(EC.element_to_be_clickable((By.ID, "content")))
            except NoSuchElementException:
                logfire.error(stmt := f"No {cls.chamber.full} member list found")
                raise Exception(stmt)

            # _, cls._tlo_session_dropdown_value = super().select_legislative_session(
            #     identifier="ddlLegislature"
            # )

            logfire.debug(f"MemberListInterface._get_member_list(): {cls.chamber.full}")
            _members_table = D_.find_element(By.ID, "dataListMembers")
            _list_of_members = _members_table.find_elements(By.TAG_NAME, "li")
            member_list = []
            for member in _list_of_members:
                _member_name = member.find_element(By.TAG_NAME, "a").text
                _member_url = member.find_element(By.TAG_NAME, "a").get_attribute(
                    "href"
                )
                _member_id = parse_qs(urlparse(_member_url).query)["Code"][0]
                member_list.append(
                    {"id": _member_id, "name": _member_name, "url": _member_url}
                )
            return member_list

    @classmethod
    @LogFireLogger.logfire_method_decorator("MemberListInterface.fetch")
    def fetch(cls, *args, **kwargs) -> Generator[Dict, None, None]:
        logfire.info(f"Fetching {cls.chamber.full} members")
        cls.navigate_to_page()
        members = cls._get_member_list()
        MemberDetailInterface.chamber = cls.chamber
        MemberDetailInterface.legislative_session = cls.legislative_session
        for member in members:
            yield MemberDetailInterface.fetch(member=member)


# MemberListInterface.chamber = HOUSE
# MemberListInterface.session = 89
#
# MemberListInterface._navigate_to_member_page()
# MemberListInterface._select_legislative_session()
# members_ = MemberListInterface._get_member_list()
# urls = MemberListInterface.fetch_member_info()
