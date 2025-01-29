from __future__ import annotations
from typing import Protocol, Optional, List, Dict
import pandas as pd


class DocumentVersionLinkProtocol(Protocol):
    pdf: Optional[str] = None
    txt: Optional[str] = None
    word_doc: Optional[str] = None

class BillStageProtocol(Protocol):
    version: str
    bill: Optional[DocumentVersionLinkProtocol] = None
    fiscal_note: Optional[DocumentVersionLinkProtocol] = None
    analysis: Optional[DocumentVersionLinkProtocol] = None
    witness_list: Optional[DocumentVersionLinkProtocol] = None
    committee_summary: Optional[DocumentVersionLinkProtocol] = None
    additional_documents: Optional[Dict[str, DocumentVersionLinkProtocol]] = None
    fiscal_impact_statements: Optional[Dict[str, DocumentVersionLinkProtocol]] = None

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
    bill_number: Optional[str] = None
    status: Optional[str] = None
    caption: Optional[str] = None
    last_action_dt: Optional[str] = None
    action_list: Optional[pd.DataFrame] = None
    stages: Optional[Dict[str, BillStageProtocol]] = None
    amendments: Optional[List[AmendmentProtocol]] = None
    additional_documents: Optional[Dict[str, DocumentVersionLinkProtocol]] = None