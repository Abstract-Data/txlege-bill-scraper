from __future__ import annotations
from typing import Optional, List, Dict, Any, Generator, Self
import re
import httpx
import asyncio
from asyncio import Future
from urllib.parse import parse_qs, urlparse, urljoin

import logfire
from bs4 import BeautifulSoup

from .bases import DetailScrapingInterface
from build_logger import LogFireLogger


class BillDetailScraper(DetailScrapingInterface):


    @classmethod
    async def get_basic_details(cls, client: httpx.AsyncClient, bill: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = await client.get(bill['bill_url'])
        except httpx.ConnectError:
            logfire.warn(f"Failed to connect to {bill['bill_url']}")
            return bill
        soup = BeautifulSoup(response.text, 'html.parser')
        bill_info = {}

        # Last Action Date
        last_action = soup.find(id="cellLastAction")
        if last_action:
            date_match = re.compile(r'\d{2}/\d{2}/\d{4}').search(last_action.text)
            bill_info['last_action_dt'] = date_match.group() if date_match else None

        # Caption Version
        caption_version = soup.find(id="cellCaptionVersion")
        if caption_version:
            bill_info['caption_version'] = caption_version.text.strip()

        # Caption Text
        caption_text = soup.find(id="cellCaptionText")
        if caption_text:
            bill_info['caption_text'] = caption_text.text.strip()

        # Author
        authors = soup.find(id="cellAuthors")
        bill_info['author'] = authors.text.strip() if authors else None

        # Sponsor
        sponsors = soup.find(id="cellSponsors")
        bill_info['sponsor'] = sponsors.text.strip() if sponsors else None

        # Subjects
        subjects = soup.find(id="cellSubjects")
        bill_info['subjects'] = [s.strip() for s in subjects.text.split('\n') if s.strip()] if subjects else []

        # Companion
        companions = soup.find(id="cellCompanions")
        if companions:
            companion_link = companions.find('a')
            if companion_link:
                href = companion_link.get('href')
                bill_info['companion'] = {
                    'companion_url': cls.build_url(href),
                    'companion_number': companion_link.text.replace(" ", "").strip(),
                    'companion_session_id': cls.links.lege_session_id
                }
            else:
                bill_info['companion'] = {}

        house_committee = await cls._get_committee_information(page_data=soup, committee_cell_tag="cellComm1")
        senate_committee = await cls._get_committee_information(page_data=soup, committee_cell_tag="cellComm2")
        bill_info['committees'] = {}
        if house_committee:
            bill_info['committees'].update(house_committee)
        if senate_committee:
            bill_info['committees'].update(senate_committee)

        bill.update(bill_info)
        return bill

    @classmethod
    async def _get_committee_information(
            cls,
            page_data: BeautifulSoup,
            committee_cell_tag: str = "cellComm1") -> Dict[str, Any] | None:
        committee_info = {}
        try:
            # House Committee
            committee_cell = page_data.find(id=f"{committee_cell_tag}Committee")
            vote_cell = page_data.find(id=f"{committee_cell_tag}Vote")
            if committee_cell:
                committee_link = committee_cell.find('a')
                committee_info['committee_chamber'] = "House" if committee_cell_tag.startswith("cellComm1") else "Senate"
                committee_info['committee_name'] = committee_link.text.strip()
                committee_info['committee_url'] = cls.build_url(committee_link.get('href'))
                committee_info['committee_session_id'] = cls.links.lege_session_id

                # Committee Status
                status_cell = page_data.find(id=f"{committee_cell_tag}Status")
                committee_info['committee_status'] = status_cell.text.strip() if status_cell else None

            # Committee Vote
            if vote_cell:
                vote_text = vote_cell.text.strip()
                ayes = re.search(r'Ayes=(\d+)', vote_text)
                nays = re.search(r'Nays=(\d+)', vote_text)
                pnv = re.search(r'Present Not Voting=(\d+)', vote_text)
                absent = re.search(r'Absent=(\d+)', vote_text)
                committee_info.setdefault(
                        'committee_votes', {
                        'ayes': int(ayes.group(1)) if ayes else 0,
                        'nays': int(nays.group(1)) if nays else 0,
                        'present_not_voting': int(pnv.group(1)) if pnv else 0,
                        'absent': int(absent.group(1)) if absent else 0
                    }
                )
            else:
                committee_info['committee_votes'] = {}
        except Exception:
            committee_info = None

        return committee_info

    @classmethod
    async def parse_bill_text_table(cls, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        versions = {'versions_url': url.replace("History.aspx", "Text.aspx")}
        text_tab_url = versions['versions_url']
        response = await client.get(text_tab_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            tables = soup.find_all("form")[1]
        except IndexError:
            logfire.warn("No bill versions found for {}".format(text_tab_url))
            return versions
        bill_table = tables.find_next("table")
        rows = bill_table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 6:
                version_info = {
                    'version': cells[0].text.strip(),
                    'version_session_id': cls.links.lege_session_id,
                    'bill_docs': [],
                    'fiscal_note_docs': [],
                    'analysis_docs': [],
                    'witness_list_docs': [],
                    'committee_summary_docs': []
                }

                # Process Bill documents (cell 1)
                bill_links = cells[1].find_all("a")
                for link in bill_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info['bill_docs'].append(
                            {
                                'version': version_info['version'],
                                'url': cls.build_url(href),
                                'type': doc_type,
                                'docs_session_id': cls.links.lege_session_id
                            }
                        )

                # Process Fiscal Note documents (cell 2)
                fiscal_links = cells[2].find_all("a")
                for link in fiscal_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info['fiscal_note_docs'].append(
                            {
                                'url': cls.build_url(href),
                                'type': doc_type
                            }
                        )

                # Process Analysis documents (cell 3)
                analysis_links = cells[3].find_all("a")
                for link in analysis_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info['analysis_docs'].append(
                            {
                                'url': cls.build_url(href),
                                'type': doc_type
                            }
                        )

                # Process Witness List documents (cell 4)
                witness_links = cells[4].find_all("a")
                for link in witness_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info['witness_list_docs'].append(
                            {
                                'url': cls.build_url(href),
                                'type': doc_type
                            }
                        )

                # Process Committee Summary documents (cell 5)
                summary_links = cells[5].find_all("a")
                for link in summary_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info['committee_summary_docs'].append(
                            {
                                'url': cls.build_url(href),
                                'type': doc_type
                            }
                        )

                versions[version_info['version']] = version_info
        return versions

    @classmethod
    async def parse_amendments_table(cls, client: httpx.AsyncClient, url: str) -> List[Dict[str, Any]]:
        amendments = []
        amendments_tab_url = (
            url
            .replace("History.aspx", "Text.aspx")
            .replace("Text.aspx", "Amendments.aspx")
        )
        response = await client.get(amendments_tab_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            tables = soup.find_all("form")[1]
        except IndexError:
            logfire.warn("No amendments found for {}".format(amendments_tab_url))
            return amendments
        amendments_table = tables.find_next("table")
        rows = amendments_table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            _coauthors_link = cells[3].find("a")
            if len(cells) >= 7:
                amendment_info = {
                    'amendment_chamber': cells[0].text.strip().split()[0],
                    'amendment_reading': cells[0].text.strip().split()[1],
                    'amendment_number': cells[1].text.strip(),
                    'amendment_author': cells[2].text.strip(),
                    'amendment_type': cells[4].text.strip(),
                    'amendment_action': cells[5].text.strip(),
                    'amendment_action_date': cells[6].text.strip(),
                    'amendment_docs': []
                }
                # Check for link in description cell
                amendment_links = cells[7].find_all("a")
                for link in amendment_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href.lower())
                        amendment_info['amendment_docs'].append(
                            {
                                'url': cls.build_url(href),
                                'type': doc_type
                            }
                        )
                if _coauthors_link:
                    _coauthor_cleaned_url = (
                        _coauthors_link
                        .get('href')
                        .replace("JavaScript:openWindow(", '')
                        .replace(')', '')
                        .split(',')[0]
                        .replace("'", '')
                    )
                    _coauthor_cleaned_url = cls.build_url('BillLookup/' + _coauthor_cleaned_url)
                    print("Coauthor Cleaned Url", _coauthor_cleaned_url)
                    co_authors_page = await client.get(_coauthor_cleaned_url)
                    co_soup = BeautifulSoup(co_authors_page.text, 'html.parser')
                    co_tables = co_soup.find_all("table", id="tblCoauthors")
                    if co_tables:
                        co_tables = co_tables[0]
                        co_rows = co_tables.find(id='cellCoauthors')
                        amendment_info['amendment_coauthors'] = [x.strip() for x in co_rows.text.split('|')]
                else:
                    amendment_info['amendment_coauthors'] = cells[3].text.strip()
                amendments.append(amendment_info)
        return amendments

    @classmethod
    async def build_detail(cls, bills) -> Self:
        pass

    @classmethod
    @LogFireLogger.logfire_method_decorator("BillDetailInterface.fetch")
    async def fetch(
            cls,
            bills: Dict[str, Dict[str, Any]],
            _client: httpx.AsyncClient,
            _sem: asyncio.Semaphore) -> Dict[str, Dict[str, Any]]:
        async def get_individual_bill(bill: Dict[str, Any]) -> Dict[str, Any]:
            async with _sem:
                bill = await cls.get_basic_details(_client, bill)
                bill['versions'] = await cls.parse_bill_text_table(_client, bill['bill_url'])
                bill['amendments'] = await cls.parse_amendments_table(_client, bill['bill_url'])
                return {bill['bill_number']: bill}
        tasks = [asyncio.create_task(get_individual_bill(m)) for m in bills.values()]
        results = await asyncio.gather(*tasks)
        return {k: v for d in results for k, v in d.items()}
