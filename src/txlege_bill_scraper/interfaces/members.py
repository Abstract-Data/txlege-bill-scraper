from __future__ import annotations

from typing import List, Dict, Self, Any
from urllib.parse import parse_qs, urlparse

import logfire
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import inject

from src.txlege_bill_scraper.bases import InterfaceBase, BrowserDriver, BrowserWait
from src.txlege_bill_scraper.protocols import HOUSE
from src.txlege_bill_scraper.build_logger import LogFireLogger

class MemberDetailInterface(InterfaceBase):

    @classmethod
    def navigate_to_page(cls, *args, **kwargs) -> Dict[str, Dict]:
        member: Dict[str, Any] | None = kwargs.get('member', None)
        if member is None:
            raise Exception("No member provided")
        with super().driver_and_wait() as (D_, W_):
            D_.get(member['url'])
            W_.until(EC.element_to_be_clickable((By.ID, "content")))
            _member_header = D_.find_element(By.ID, "usrHeader_lblPageTitle")
            _member_first_name = (
                _member_header.text
                  .split(
                    cls.chamber.pfx)[-1]
                .replace(member['name'], "")
                .strip()
            )
            member['first_name'] = _member_first_name

            try:
                _contact_info = D_.find_element(By.ID, "contactInfo")
                with super().get_text_by_label_context(_contact_info) as get_:
                    member['district'] = get_("lblDistrict")
                    member['capitol_office'] = get_("lblCapitolOffice")
                    member['capitol_address1'] = get_("lblCapitolAddress1")
                    member['capitol_address2'] = get_("lblCapitolAddress2")
                    member['capitol_phone'] = get_("lblCapitolPhone")
                    member['district_address1'] = get_("lblDistrictAddress1")
                    member['district_address2'] = get_("lblDistrictAddress2")
                    member['district_phone'] = get_("lblDistrictPhone")
            except NoSuchElementException:
                pass

            _legislative_info = D_.find_element(By.ID, "legislativeInformation")
            _legislative_links = _legislative_info.find_elements(By.TAG_NAME, "a")
            get_url_ = lambda txt: next((x.get_attribute("href") for x in _legislative_links if txt in x.text), None)
            member['bills_authored_url'] = get_url_("Bills Authored")
            member['bills_sponsored_url'] = get_url_("Bills Sponsored")
            member['bills_coauthored_url'] = get_url_("Bills Coauthored")
            member['bills_cosponsored_url'] = get_url_("Bills Cosponsored")
            member['amendments_authored_url'] = get_url_("Amendments Authored")
            member = cls.get_bill_numbers(member)
        return member

    @classmethod
    def get_bill_numbers(cls, member: Dict) -> Dict | None:
        with super().driver_and_wait() as (D_, W_):
            _urls = {k: v for k, v in member.items() if k.endswith("_url")}
            W_ = WebDriverWait(D_, 2)
            for _type, url in _urls.items():
                D_.get(url)
                try:
                    W_.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    _bill_table = D_.find_element(By.TAG_NAME, "table")
                    _bill_urls = _bill_table.find_elements(By.TAG_NAME, "a")
                    bill_type_list = []
                    for _bill in _bill_urls:
                        _bill_number = _bill.get_attribute("href")
                        _session = parse_qs(urlparse(_bill_number).query)['LegSess'][0]
                        _bill_num = parse_qs(urlparse(_bill_number).query)['Bill'][0]
                        bill_type_list.append(f"{_session}_{_bill_num}")
                    member[_type.replace('_url', '')] = bill_type_list
                except Exception:
                    continue
                return member


class MemberListInterface(InterfaceBase):

    @classmethod
    @LogFireLogger.logfire_method_decorator("MemberListInterface._navigate_to_member_page")
    def navigate_to_page(cls):
        with super().driver_and_wait() as (D_, W_):
            logfire.debug(f"Navigating to {cls.chamber.full} member page")

            D_.get(cls._base_url)
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{cls.chamber.full}"))).click()
            W_.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{cls.chamber.full} Members"))).click()

    @classmethod
    def _get_member_list(cls) -> List[Dict]:
        with super().driver_and_wait() as (D_, W_):
            try:
                W_.until(EC.element_to_be_clickable((By.ID, "content")))
            except NoSuchElementException:
                logfire.error(f"No {cls.chamber.full} member list found")
                raise Exception(f"No {cls.chamber.full} member list found")
            logfire.debug(f"MemberListInterface._get_member_list(): {cls.chamber.full}")
            _members_table = D_.find_element(By.ID, "dataListMembers")
            _list_of_members = _members_table.find_elements(By.TAG_NAME, "li")
            member_list = []
            for member in _list_of_members:
                _member_name = member.find_element(By.TAG_NAME, "a").text
                _member_url = member.find_element(By.TAG_NAME, "a").get_attribute("href")
                _member_id = parse_qs(urlparse(_member_url).query)['Code'][0]
                member_list.append({
                    'id': _member_id,
                    'name': _member_name,
                    'url': _member_url
                })
            return member_list

    @classmethod
    @LogFireLogger.logfire_method_decorator("MemberListInterface.fetch_member_info")
    def fetch_member_info(cls) -> List[Dict]:

        # with logfire_context(f"MemberInterface.fetch_member_info({cls.chamber.full})"):
        cls.navigate_to_page()
        members = cls._get_member_list()
        MemberDetailInterface.chamber = cls.chamber
        MemberDetailInterface.legislative_session = cls.legislative_session
        _members = list(map(lambda x: MemberDetailInterface.navigate_to_page(member=x), members))
        return _members

# MemberListInterface.chamber = HOUSE
# MemberListInterface.session = 89
#
# MemberListInterface._navigate_to_member_page()
# MemberListInterface._select_legislative_session()
# members_ = MemberListInterface._get_member_list()
# urls = MemberListInterface.fetch_member_info()