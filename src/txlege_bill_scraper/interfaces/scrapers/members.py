from __future__ import annotations

from asyncio import Future
from typing import Self, Dict, Any, List
import httpx
import asyncio
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup

from protocols import HttpsValidatedURL
from .bases import DetailScrapingInterface
from models.members import MemberDetails, MemberAddress, MemberBillTypeURLs


#TODO: Create way to assign member ID to type of bill condition they're involved with.
# May need to create a new model for BillInvolvement and an enum for Involvement Type.

class MemberDetailScraper(DetailScrapingInterface):

    def __init__(self):
        super().__init__()

    def build_detail(self) -> Self:
        pass

    @classmethod
    async def get_member_info(cls, client: httpx.AsyncClient, member: MemberDetails) -> MemberDetails:
        request = await client.get(member.member_url.__str__())
        soup = BeautifulSoup(request.text, 'html.parser')
        # Header Cleanup
        _remove_information_pfx = f"Information for Rep."
        _member_header = soup.find(id="usrHeader_lblPageTitle")
        _member_header_text = _member_header.text.replace(_remove_information_pfx, "").strip()

        # Name Cleanup
        member.last_name = member.name
        member.first_name = _member_header_text.replace(member.last_name, "").strip()
        if member.first_name and member.last_name:
            del member.name

        # Contact Information Extraction
        _contact_info = soup.find(id="contactInfo")
        if _contact_info:
            member.member_district = _contact_info.find(id="lblDistrict").text.strip()
            member.member_capitol_office = _contact_info.find(id="lblCapitolOffice").text.strip()
            _capitol_address = {
                'address1': _contact_info.find(id="lblCapitolAddress1").text.strip(),
                'address2': _contact_info.find(id="lblCapitolAddress2").text.strip(),
                'phone': _contact_info.find(id="lblCapitolPhone").text.strip()
            }

            _district_address = {
                'address1': _contact_info.find(id="lblDistrictAddress1").text.strip(),
                'address2': _contact_info.find(id="lblDistrictAddress2").text.strip(),
                'phone': _contact_info.find(id="lblDistrictPhone").text.strip()
            }

            member.district_address = MemberAddress(**_district_address) if any(_district_address.values()) else None
            member.capitol_address = MemberAddress(**_capitol_address) if any(_capitol_address.values()) else None

        # Legislative Information Extraction
        _legislative_info = soup.find(id="legislativeInformation")
        if _legislative_info:
            _legislative_links = _legislative_info.find_all('a')
            get_url_ = lambda txt: next(
                (
                    cls.links._base_url + x['href'].replace('..', '')
                    for x in _legislative_links if txt in x.text
                ), None)
            member.bill_urls = MemberBillTypeURLs(
                authored_url=get_url_("Bills Authored"),
                sponsored_url=get_url_("Bills Sponsored"),
                coauthored_url=get_url_("Bills Coauthored"),
                cosponsored_url=get_url_("Bills Cosponsored"),
                amendments_authored_url=get_url_("Amendments Authored")
            )
        return member

    @classmethod
    async def get_member_bill_urls(cls, client: httpx.AsyncClient, member: MemberDetails) -> MemberDetails | None:
        bill_type_list = {}
        for _type, url in member.bill_urls.model_dump().items():
            response = await client.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            _bill_table = soup.find_all('table')
            _type_dict = bill_type_list.setdefault(_type.replace('_url', ""), {})
            for _bill in _bill_table:
                _bill_url = _bill.find('a')
                if not _bill_url:
                    continue
                _bill_url = _bill_url['href']
                try:
                    _session = parse_qs(urlparse(_bill_url).query)["LegSess"][0]
                    _bill_num = parse_qs(urlparse(_bill_url).query)["Bill"][0]
                except KeyError:
                    continue
                _type_dict[_bill_num] = _bill_url
        member.bills = bill_type_list
        return member

    @classmethod
    async def fetch(
            cls,
            members: Dict[str, MemberDetails],
            _client: httpx.AsyncClient,
            _sem: asyncio.Semaphore) -> List[MemberDetails]:
        counter = 0
        async def get_individual_member(_m: MemberDetails):
            async with _sem:
                _m = await cls.get_member_info(_client, _m)
                _m = await cls.get_member_bill_urls(_client, _m)
                nonlocal counter
                counter += 1
                if counter % 10 == 0:
                    print(f"Processed {counter} members")
                return _m
        tasks = [
            asyncio.create_task(get_individual_member(m)) for m in members.values()
        ]
        results = await asyncio.gather(*tasks)
        return results