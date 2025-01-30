from typing import Protocol, Optional, List, Dict
from datetime import date, time

from .committees import CommitteeDetailsProtocol, CommitteeBillStatusProtocol


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

class BillActionProtocol(Protocol):
    chamber: str
    description: str
    comment: Optional[str]
    date: Optional[date]
    time: Optional[time]
    journal_page: Optional[str]
    url: Optional[str]


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
    caption_version: Optional[str] = None
    caption_text: Optional[str] = None
    last_action_dt: Optional[str] = None
    action_list: Optional[list] = None
    stages: Optional[Dict[str, BillStageProtocol]] = None
    amendments: Optional[List[AmendmentProtocol]] = None
    additional_documents: Optional[Dict[str, DocumentVersionLinkProtocol]] = None
    house_committee: Optional[CommitteeDetailsProtocol] = None
    house_committee_status: Optional[Dict[str, CommitteeBillStatusProtocol]] = None
    senate_committee: Optional[CommitteeDetailsProtocol] = None
    senate_committee_status: Optional[Dict[str, CommitteeBillStatusProtocol]] = None