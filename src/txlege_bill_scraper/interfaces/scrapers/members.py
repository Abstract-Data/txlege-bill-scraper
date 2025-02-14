from __future__ import annotations

from asyncio import Future
from typing import Self, Dict, Any
import httpx
import asyncio
from urllib.parse import parse_qs, urlparse
from bs4 import BeautifulSoup
from .bases import DetailScrapingInterface


class MemberDetailScraper(DetailScrapingInterface):

    def build_detail(self) -> Self:
        pass

    @classmethod
    async def get_member_info(cls, client: httpx.AsyncClient, member: Dict) -> dict:
        request = await client.get(member['member_url'])
        soup = BeautifulSoup(request.text, 'html.parser')
        # Header Cleanup
        _remove_information_pfx = f"Information for Rep."
        _member_header = soup.find(id="usrHeader_lblPageTitle")
        _member_header_text = _member_header.text.replace(_remove_information_pfx, "").strip()

        # Name Cleanup
        member["last_name"] = member["name"]
        member["first_name"] = _member_header_text.replace(member["last_name"], "").strip()
        if "first_name" in member and "last_name" in member:
            del member["name"]

        # Contact Information Extraction
        _contact_info = soup.find(id="contactInfo")
        if _contact_info:
            member["district"] = _contact_info.find(id="lblDistrict").text.strip()
            member["capitol_office"] = _contact_info.find(id="lblCapitolOffice").text.strip()
            member["capitol_address1"] = _contact_info.find(id="lblCapitolAddress1").text.strip()
            member["capitol_address2"] = _contact_info.find(id="lblCapitolAddress2").text.strip()
            member["capitol_phone"] = _contact_info.find(id="lblCapitolPhone").text.strip()
            member["district_address1"] = _contact_info.find(id="lblDistrictAddress1").text.strip()
            member["district_address2"] = _contact_info.find(id="lblDistrictAddress2").text.strip()
            member["district_phone"] = _contact_info.find(id="lblDistrictPhone").text.strip()

        # Legislative Information Extraction
        _legislative_info = soup.find(id="legislativeInformation")
        if _legislative_info:
            _legislative_links = _legislative_info.find_all('a')
            get_url_ = lambda txt: next(
                (
                    cls.links._base_url + x['href'].replace('..', '')
                    for x in _legislative_links if txt in x.text
                ), None)
            member["bills_authored_url"] = get_url_("Bills Authored")
            member["bills_sponsored_url"] = get_url_("Bills Sponsored")
            member["bills_coauthored_url"] = get_url_("Bills Coauthored")
            member["bills_cosponsored_url"] = get_url_("Bills Cosponsored")
            member["amendments_authored_url"] = get_url_("Amendments Authored")
        return member

    @classmethod
    async def get_member_bill_urls(cls, client: httpx.AsyncClient, member: Dict) -> Dict | None:
        bill_urls = {k: v for k, v in member.items() if k.endswith("_url") and k.startswith("bills")}
        bill_type_list = {}
        for _type, url in bill_urls.items():
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
        member['bills'] = bill_type_list
        return member

    @classmethod
    async def fetch(
            cls,
            members: Dict[str, Dict[str, str]],
            _client: httpx.AsyncClient,
            _sem: asyncio.Semaphore) -> Dict[str, Dict[str, str]]:
        async def get_individual_member(_m: Dict[str, str]):
            async with _sem:
                _m = await cls.get_member_info(_client, _m)
                _m = await cls.get_member_bill_urls(_client, _m)
                return _m
        tasks = [
            asyncio.create_task(get_individual_member(dict(m))) for m in members.values()
        ]
        results = await asyncio.gather(*tasks)
        return results