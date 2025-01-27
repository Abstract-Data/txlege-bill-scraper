from __future__ import annotations
from typing import Optional, List, Dict

from pydantic import Field as PydanticField
import pandas as pd

from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.bases import DBModelBase, NonDBModelBase


class BillStage(DBModelBase):
    version: str
    pdf: str
    txt: str
    word_doc: str
    fiscal_note: Optional[str] = None
    analysis: Optional[str] = None
    witness_list: Optional[str] = None
    summary_of_action: Optional[str] = None


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
    stages: Optional[List[BillStage]] = None
    amendments: Optional[List[Amendment]] = None


class BillList(NonDBModelBase):
    chamber: ChamberTuple
    bills: Optional[Dict[str, BillDetail]] = PydanticField(default_factory=dict)

    # Move this method elsewhere or inject the interface
    def create_bill_list(self):
        from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        self.bills = BillListInterface._build_bill_list(chamber=self.chamber)

    def create_bill_details(self):
        from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        self.bills = BillListInterface._build_bill_details(self.bills)