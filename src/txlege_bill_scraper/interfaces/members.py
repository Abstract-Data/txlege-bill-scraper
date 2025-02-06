from __future__ import annotations

from typing import List, Dict, Self
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

logfire_context = LogFireLogger.logfire_context

class MemberDetailInterface(InterfaceBase):

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _member_contact_page(cls, member: Dict, _driver: BrowserDriver, _wait: BrowserWait) -> Dict[str, Dict]:
        _driver.get(member['url'])
        _wait.until(EC.element_to_be_clickable((By.ID, "content")))
        _member_header = _driver.find_element(By.ID, "usrHeader_lblPageTitle")
        _member_first_name = (
            _member_header.text
              .split(
                cls.chamber.pfx)[-1]
            .replace(member['name'], "")
            .strip()
        )
        member['first_name'] = _member_first_name

        try:
            _contact_info = _driver.find_element(By.ID, "contactInfo")
            with cls.get_text_by_label_context(_contact_info) as get_:
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

        _legislative_info = _driver.find_element(By.ID, "legislativeInformation")
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
    @inject.params(_driver=BrowserDriver)
    def get_bill_numbers(cls, member: Dict, _driver: BrowserDriver) -> Dict:
        _urls = {k: v for k, v in member.items() if k.endswith("_url")}
        _wait = WebDriverWait(_driver, 2)
        for _type, url in _urls.items():
            _driver.get(url)
            try:
                _wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                _bill_table = _driver.find_element(By.TAG_NAME, "table")
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
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _navigate_to_member_page(
            cls,
            _driver: BrowserDriver,
            _wait: BrowserWait):

        logfire.debug(f"Navigating to {cls.chamber.full} member page")

        _driver.get(cls._base_url)
        _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{cls.chamber.full}"))).click()
        _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, f"{cls.chamber.full} Members"))).click()

    @classmethod
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def _get_member_list(cls, _driver: BrowserDriver, _wait: BrowserWait) -> List[Dict]:
        try:
            _wait.until(EC.element_to_be_clickable((By.ID, "content")))
        except NoSuchElementException:
            logfire.error(f"No {cls.chamber.full} member list found")
            raise Exception(f"No {cls.chamber.full} member list found")
        logfire.debug(f"MemberListInterface._get_member_list(): {cls.chamber.full}")
        _members_table = _driver.find_element(By.ID, "dataListMembers")
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
    @inject.params(_driver=BrowserDriver, _wait=BrowserWait)
    def fetch_member_info(cls, _driver: BrowserDriver, _wait: BrowserWait) -> List[Dict]:

        with logfire_context(f"MemberInterface.fetch_member_info({cls.chamber.full})"):
            cls._navigate_to_member_page()
            members = cls._get_member_list()
            MemberDetailInterface.chamber = cls.chamber
            MemberDetailInterface.legislative_session = cls.legislative_session
            _members = list(map(lambda x: MemberDetailInterface._member_contact_page(x), members))
        return _members

# MemberListInterface.chamber = HOUSE
# MemberListInterface.session = 89
#
# MemberListInterface._navigate_to_member_page()
# MemberListInterface._select_legislative_session()
# members_ = MemberListInterface._get_member_list()
# urls = MemberListInterface.fetch_member_info()