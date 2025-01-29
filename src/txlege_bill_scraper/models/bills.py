from __future__ import annotations
from typing import Optional, List, Dict

from pydantic import Field as PydanticField
from sqlmodel import Field as SQLModelField
import pandas as pd
from selenium.webdriver.common.virtual_authenticator import Protocol

from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.bases import DBModelBase, NonDBModelBase

class DocumentVersionLink(DBModelBase):
    pdf: Optional[str] = None
    txt: Optional[str] = None
    word_doc: Optional[str] = None

class BillStage(DBModelBase):
    version: str
    bill: Optional[DocumentVersionLink] = None
    fiscal_note: Optional[DocumentVersionLink] = None
    analysis: Optional[DocumentVersionLink] = None
    witness_list: Optional[DocumentVersionLink] = None
    committee_summary: Optional[DocumentVersionLink] = None
    fiscal_impact_statements: Optional[Dict[str, DocumentVersionLink]] = None


class Amendment(DBModelBase):
    reading: str
    number: str
    author: str
    coauthors: Optional[str] = None
    amendment_type: str
    action: str
    action_date: str
    html_link: Optional[str] = None
    pdf_link: Optional[str] = None


class BillDetail(DBModelBase):
    bill_url: str
    bill_number: Optional[str] = None
    status: Optional[str] = None
    caption: Optional[str] = None
    last_action_dt: Optional[str] = None
    action_list: Optional[pd.DataFrame] = None
    stages: Optional[Dict[str, BillStage]] = SQLModelField(default_factory=dict)
    amendments: Optional[List[Amendment]] = None
    additional_documents: Optional[Dict[str, DocumentVersionLink]] = None


class BillList(NonDBModelBase):
    chamber: ChamberTuple
    legislative_session: str
    bills: Optional[Dict[str, BillDetail]] = PydanticField(default_factory=dict)

    # Move this method elsewhere or inject the interface
    def create_bill_list(self):
        from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        self.bills = BillListInterface._build_bill_list(chamber=self.chamber, lege_session=self.legislative_session)

    def create_bill_details(self):
        from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        self.bills = BillListInterface._build_bill_details(self.bills)