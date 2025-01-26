from __future__ import annotations
from typing import Optional, List, Dict, Tuple, Self

from pydantic import Field as PydanticField
import pandas as pd

from types_ import ChamberTuple
from bases import DBModelBase, InterfaceBase, NonDBModelBase
from navigator import BillListInterface, BillDetailInterface


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

    def get_bill_list(self):
        self.bills = BillListInterface().create_bill_list(chamber=self.chamber)