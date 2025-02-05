from functools import partial
from typing import Dict, Optional

from sqlmodel import JSON, Field as SQLModelField

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .bases import (
    DBModelBase,
    get_link
)


class LegislatorBase(DBModelBase):
    id: str = SQLModelField(primary_key=True)
    member_url: str
    prefix: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    district: Optional[str] = None
    capitol_office: Optional[str] = None
    capitol_phone: Optional[str] = None
    urls: Dict[str, str] = SQLModelField(default_factory=dict, sa_type=JSON)
    # bills_authored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_sponsored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_coauthored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # bills_cosponsored: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # amendments_authored: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def __init__(self, **data):
        if not self.driver:
            self.__class__.configure_driver()
        super().__init__(**data)

    def fetch_member_details(self):
        with self.driver as _driver:
            _driver.get(self.member_url)
            _wait = WebDriverWait(_driver, 10)
            _get_link = partial(get_link, _driver=_driver)
            _wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Bills Authored")))
            member_name = (
                _driver
                .find_element(By.ID, "usrHeader_lblPageTitle")
                .text
                .replace("Information For", "")
                .strip()
            )
            if 'Rep' in member_name:
                self.prefix = 'REPRESENTATIVE'
                self.district = "HD "
                member_name = member_name.replace("Rep. ", "")
            elif 'Sen' in member_name:
                self.prefix = 'SENATOR'
                self.prefix = "SD "
                member_name = member_name.replace("Sen. ", "")

            member_contact = _driver.find_element(By.ID, "contactInfo")
            self.district += member_contact.find_element(By.ID, "lblDistrict").text
            _split_member_name = member_name.split()
            if len(_split_member_name) == 2:
                self.last_name = _split_member_name[1]
                self.first_name = _split_member_name[0]
            if len(_split_member_name) == 3:
                if len(_split_member_name[1]) == 1:
                    self.first_name = f"{_split_member_name[0]} {_split_member_name[1]}"
                    self.last_name = _split_member_name[2]
                else:
                    self.first_name = _split_member_name[0]
                    self.last_name = f"{_split_member_name[1]} {_split_member_name[2]}"
            self.capitol_office = member_contact.find_element(By.ID, "lblCapitolOffice").text
            self.capitol_phone = member_contact.find_element(By.ID, "lblCapitolPhone").text
            self.urls = {
                'authored': _get_link("Bills Authored"),
                'sponsored': _get_link("Bills Sponsored"),
                'co-authored': _get_link("Bills Coauthored"),
                'co-sponsored': _get_link("Bills Cosponsored"),
                'amendments': _get_link("Amendments Authored")
            }
        return self