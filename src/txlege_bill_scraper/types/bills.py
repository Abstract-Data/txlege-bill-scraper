from __future__ import annotations
from typing import Protocol, Optional, List
import pandas as pd

class BillStageProtocol(Protocol):
    version: str
    pdf: str
    txt: str
    word_doc: str
    fiscal_note: Optional[str]
    analysis: Optional[str]
    witness_list: Optional[str]
    summary_of_action: Optional[str]

class AmendmentProtocol(Protocol):
    reading: str
    number: str
    author: str
    coauthors: Optional[str]
    amendment_type: str
    action: str
    action_date: str
    html_link: Optional[str]
    pdf_link: Optional[str]

class BillDetailProtocol(Protocol):
    bill_url: str
    bill_number: Optional[str]
    status: Optional[str]
    caption: Optional[str]
    last_action_dt: Optional[str]
    action_list: Optional[pd.DataFrame]
    stages: Optional[List[BillStageProtocol]]
    amendments: Optional[List[AmendmentProtocol]]