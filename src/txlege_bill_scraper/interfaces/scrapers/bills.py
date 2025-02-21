from __future__ import annotations
from typing import Optional, List, Dict, Any, Generator, Self
import re
import httpx
import asyncio
from icecream import ic
from asyncio import Future
from urllib.parse import parse_qs, urlparse, urljoin
from datetime import datetime

import logfire
from bs4 import BeautifulSoup, Tag as BeautifulSoupTag

from txlege_bill_scraper.protocols import ScrapedPageElement, ScrapedPageContainer
from .bases import DetailScrapingInterface
from txlege_bill_scraper.models.bills import (
    BillDoc,
    TXLegeBill,
    BillAmendment,
    BillVersion,
    BillAction,
    BillCompanion,
    BillDocDescription,
    CommitteeDetails,
    CommitteeVote,
)
from build_logger import LogFireLogger
from pydantic import ValidationError


class BillDetailScraper(DetailScrapingInterface):
    @classmethod
    async def get_basic_details(
        cls, client: httpx.AsyncClient, bill: TXLegeBill
    ) -> TXLegeBill:
        try:
            response = await client.get(bill.bill_url.__str__())
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            _form1 = soup.find("form", {"id": "Form1"})

            # Last Action Date
            bill.last_action_dt = _form1.find(id="cellLastAction")

            # Caption Version
            bill.caption_version = _form1.find(id="cellCaptionVersion")

            # Caption Text
            bill.caption_text = _form1.find(id="cellCaptionText")

            # Author
            bill.authors = _form1.find(id="cellAuthors")
            # bill.authors = authors.text.strip() if authors else None

            # Sponsor
            bill.sponsors = _form1.find(id="cellSponsors")

            # Subjects
            subjects = _form1.find(id="cellSubjects")
            bill.subjects = (
                [s.strip() for s in subjects.text.split("<br>") if s.strip()]
                if subjects
                else []
            )

            # Companion
            companions = _form1.find(id="cellCompanions")
            if companions:
                companion_link = companions.find("a")
                if companion_link:
                    href = companion_link.get("href")
                    bill.companions.append(
                        BillCompanion(
                            companion_url=cls.build_url(href),
                            companion_bill_number=companion_link.text.replace(
                                " ", ""
                            ).strip(),
                            companion_session_id=cls.links.lege_session_id,
                        )
                    )
                else:
                    bill.companions = None

            house_committee = await cls._get_committee_information(
                page_data=soup, bill=bill, committee_cell_tag="cellComm1"
            )
            senate_committee = await cls._get_committee_information(
                page_data=soup, bill=bill, committee_cell_tag="cellComm2"
            )
            if house_committee:
                bill.committees.append(house_committee)
            if senate_committee:
                bill.committees.append(senate_committee)
            return bill
        except Exception as e:
            if isinstance(e, ValidationError):
                ic(f"Validation Error for {bill.bill_number}: {e}")
                logfire.error(f"Validation Error on {bill.bill_number}: {e}")
            logfire.error(f"Failed to process {bill.bill_number}: {e}")

    @classmethod
    async def _get_committee_information(
        cls,
        page_data: BeautifulSoup,
        bill: TXLegeBill,
        committee_cell_tag: str = "cellComm1",
    ) -> Optional[str]:
        try:
            # House Committee
            committee_cell = page_data.find(id=f"{committee_cell_tag}Committee")
            vote_cell = page_data.find(id=f"{committee_cell_tag}CommitteeVote")
            if committee_cell:
                committee_link = committee_cell.find("a")
                _committee_url = cls.build_url(committee_link.get("href"))
                _committee_id = parse_qs(urlparse(_committee_url).query)["CmteCode"][0]
                _committee_exists = _committee_id in cls.links.committees
                if not _committee_exists:
                    raise Exception(
                        f"Committee {_committee_id} not found in committee list"
                    )
                cls.links.committees[_committee_id].committee_bills.append(
                    bill.bill_number)
                # committee_info['committee_chamber'] = "House" if committee_cell_tag.startswith("cellComm1") else "Senate"
                # committee_info['committee_name'] = committee_link.text.strip()
                # committee_info['committee_url'] = cls.build_url(committee_link.get('href'))
                # committee_info['committee_id'] = parse_qs(urlparse(_committee_url).query)["CmteCode"][0]

                # Committee Status
                status_cell = page_data.find(id=f"{committee_cell_tag}Status")
                # committee_info['committee_status'] = status_cell.text.strip() if status_cell else None

                # Committee Vote
                if vote_cell:
                    vote_text = vote_cell.text.strip()
                    ayes = re.search(r"Ayes=(\d+)", vote_text)
                    nays = re.search(r"Nays=(\d+)", vote_text)
                    pnv = re.search(r"Present Not Voting=(\d+)", vote_text)
                    absent = re.search(r"Absent=(\d+)", vote_text)
                    _data = {
                        'committee_id': _committee_id,
                        'bill_id': bill.bill_id,
                        'ayes': int(ayes.group(1)) if ayes else 0,
                        'nays': int(nays.group(1)) if nays else 0,
                        'present_not_voting': int(pnv.group(1)) if pnv else 0,
                        'absent': int(absent.group(1)) if absent else 0
                    }
                    (cls.links
                    .committees[_committee_id]
                    .committee_votes[bill.bill_number]) = CommitteeVote(**_data)
                # committee_info.setdefault(
                #         'committee_votes', {
                #         'ayes': int(ayes.group(1)) if ayes else 0,
                #         'nays': int(nays.group(1)) if nays else 0,
                #         'present_not_voting': int(pnv.group(1)) if pnv else 0,
                #         'absent': int(absent.group(1)) if absent else 0
                #     }
                # )
                return _committee_id
            # TODO: Turn 'Bills Voted On' into a list instead of a dict.
        except Exception:
            committee_info = None

    @classmethod
    async def parse_bill_text_table(
        cls, client: httpx.AsyncClient, bill: TXLegeBill
    ) -> Dict[str, BillVersion]:
        versions_url = bill.bill_url.__str__().replace("History.aspx", "Text.aspx")
        text_tab_url = versions_url.__str__()
        max_retries = 5
        retries = 0
        versions = {}
        soup = await cls.fetch_with_retries(client=client, url=text_tab_url)
        if not soup:
            return versions
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
                version_info = BillVersion(
                    version=cells[0].text.strip(),
                )
                # Process Bill documents (cell 1)
                bill_links = cells[1].find_all("a")
                for link in bill_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info.bill_docs.append(
                            BillDoc(
                                version=version_info.version,
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.BILL_TEXT,
                            )
                        )

                # Process Fiscal Note documents (cell 2)
                fiscal_links = cells[2].find_all("a")
                for link in fiscal_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info.fiscal_note_docs.append(
                            BillDoc(
                                version=version_info.version,
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.FISCAL_NOTE,
                            )
                        )

                # Process Analysis documents (cell 3)
                analysis_links = cells[3].find_all("a")
                for link in analysis_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info.analysis_docs.append(
                            BillDoc(
                                versions=version_info.version,
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.ANALYSIS,
                            )
                        )

                # Process Witness List documents (cell 4)
                witness_links = cells[4].find_all("a")
                for link in witness_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info.witness_list_docs.append(
                            BillDoc(
                                version=version_info.version,
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.WITNESS_LIST,
                            )
                        )

                # Process Committee Summary documents (cell 5)
                summary_links = cells[5].find_all("a")
                for link in summary_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href)
                        version_info.committee_summary_docs.append(
                            BillDoc(
                                version=version_info.version,
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.SUMMARY,
                            )
                        )

                versions[version_info.version] = version_info
        return versions

    @classmethod
    async def parse_bill_actions_table(cls, client: httpx.AsyncClient, bill: TXLegeBill) -> List[BillAction]:
        actions = []
        actions_tab_url = bill.bill_url.__str__().replace("History.aspx", "Actions.aspx")
        soup = await cls.fetch_with_retries(client=client, url=actions_tab_url)
        tables = soup.find_all("form")[1]
        actions_table = tables.find_all("table")[1]
        rows = actions_table.find_all("tr")[1:]
        row_data = {}
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 3:
                _data = BillAction(
                    **{
                        'bill_id': bill.bill_id,
                        'tier': cells[0].text.strip(),
                        'description': cells[1].text.strip(),
                        'description_url': cells[1].find("a").get("href") if cells[1].find("a") else None,
                        'comment': cells[2].text.strip() if cells[2].text.strip() else None,
                        'date': datetime.strptime(
                            cells[3].text.strip(),
                            '%m/%d/%Y').date() if len(cells) >= 4 and cells[3].text.strip() else None,
                        'time': datetime.strptime(
                            cells[4].text.strip(),
                            "%I:%M %p").time() if len(cells) >= 5 and cells[4].text.strip() else None,
                        'journal_page': cells[5].text.strip() if len(cells) >= 6 and cells[5].text.strip() else None,
                    }
                )
                actions.append(_data)
        return actions


    @classmethod
    async def parse_amendments_table(
        cls, client: httpx.AsyncClient, bill: TXLegeBill
    ) -> List[BillAmendment]:
        amendments = []
        amendments_tab_url = (
            bill.bill_url.__str__()
            .replace("History.aspx", "Text.aspx")
            .replace("Text.aspx", "Amendments.aspx")
        )
        soup = await cls.fetch_with_retries(client=client, url=amendments_tab_url)
        try:
            tables = soup.find_all("form")[1]
        except IndexError:
            logfire.warn("No amendments found for {}".format(amendments_tab_url))
            return bill

        amendments_table = tables.find_next("table")
        rows = amendments_table.find_all("tr")[1:]
        for row in rows:
            cells = row.find_all("td")
            _coauthors_link = cells[3].find("a")
            if len(cells) >= 7:
                amendment_info: BillAmendment = BillAmendment(
                    bill_number=bill.bill_number,
                    chamber=cells[0].text.strip().split()[0],
                    reading=cells[0].text.strip().split()[1],
                    number=cells[1].text.strip(),
                    author=cells[2].text.strip(),
                    type_=cells[4].text.strip(),
                    action=cells[5].text.strip(),
                    action_date=cells[6].text.strip(),
                )
                # Check for link in description cell
                amendment_links = cells[7].find_all("a")
                for link in amendment_links:
                    href = link.get("href")
                    if href:
                        doc_type = cls.get_document_type(href.lower())
                        amendment_info.docs.append(
                            BillDoc(
                                doc_url=cls.build_url(href),
                                doc_type=doc_type,
                                doc_description=BillDocDescription.AMENDMENT,
                            )
                        )
                if _coauthors_link:
                    _coauthor_cleaned_url = (
                        _coauthors_link.get("href")
                        .replace("JavaScript:openWindow(", "")
                        .replace(")", "")
                        .split(",")[0]
                        .replace("'", "")
                    )
                    _coauthor_cleaned_url = cls.build_url(
                        "BillLookup/" + _coauthor_cleaned_url
                    )
                    co_authors_page = await client.get(_coauthor_cleaned_url)
                    co_soup = BeautifulSoup(co_authors_page.text, "html.parser")
                    co_tables = co_soup.find_all("table", id="tblCoauthors")
                    if co_tables:
                        co_tables = co_tables[0]
                        co_rows = co_tables.find(id="cellCoauthors")
                        amendment_info.co_authors = [
                            x.strip() for x in co_rows.text.split("|")
                        ]
                else:
                    amendment_info.co_authors = cells[3].text.strip()
                amendments.append(amendment_info)
        return amendments

    @classmethod
    async def build_detail(cls, bills) -> Self:
        pass

    @classmethod
    @LogFireLogger.logfire_method_decorator("BillDetailInterface.fetch")
    async def fetch(
        cls,
        bills: Dict[str, TXLegeBill],
        _client: httpx.AsyncClient,
        _sem: asyncio.Semaphore,
    ) -> Dict[str, TXLegeBill]:
        counter = 0

        async def get_individual_bill(bill: TXLegeBill) -> Dict[str, TXLegeBill]:
            async with _sem:
                try:
                    bill = await cls.get_basic_details(client=_client, bill=bill)
                    bill.versions = await cls.parse_bill_text_table(
                        client=_client, bill=bill
                    )
                    bill.actions = await cls.parse_bill_actions_table(
                        client=_client, bill=bill
                    )
                    bill.amendments = await cls.parse_amendments_table(
                        client=_client, bill=bill
                    )
                    bill.create_ids()
                    nonlocal counter
                    counter += 1
                    if counter % 250 == 0:
                        print(f"Processed {counter} bills")
                except Exception as e:
                    logfire.error(f"Failed to process {bill.bill_number}: {e}")
                return {bill.bill_number: bill}

        tasks = [asyncio.create_task(get_individual_bill(m)) for m in bills.values()]
        results = await asyncio.gather(*tasks)
        return {k: v for d in results for k, v in d.items()}
