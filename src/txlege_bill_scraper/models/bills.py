from typing import Optional, Dict, ClassVar
from datetime import datetime, date, time
from pydantic import Field as PydanticField, HttpUrl
from sqlmodel import Field as SQLModelField, Relationship
import pandas as pd
from src.txlege_bill_scraper.build_logger import LogFireLogger

logfire_context = LogFireLogger.logfire_context

from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.bases import DBModelBase, NonDBModelBase
from src.txlege_bill_scraper.models.committees import CommitteeDetails, CommitteeBillStatus

class DocumentVersionLink(DBModelBase, table=True):
    document_version_link_id: int = SQLModelField(primary_key=True)
    pdf: Optional[str] = None
    txt: Optional[str] = None
    word_doc: Optional[str] = None

class FiscalImpactStatement(DBModelBase, table=True):
    fiscal_impact_statement_id: int = SQLModelField(primary_key=True)
    version: str
    released_by: str
    documents: DocumentVersionLink = Relationship(back_populates="fiscal_impact_statements")

class BillStage(DBModelBase, table=True):
    bill_stage_id: int = SQLModelField(primary_key=True)
    version: str
    bill: Optional[DocumentVersionLink] = Relationship(back_populates="bill_stage")
    fiscal_note: Optional[DocumentVersionLink] = Relationship(back_populates="bill_stage")
    analysis: Optional[DocumentVersionLink] = Relationship(back_populates="bill_stage")
    witness_list: Optional[DocumentVersionLink] = Relationship(back_populates="bill_stage")
    committee_summary: Optional[DocumentVersionLink] = Relationship(back_populates="bill_stage")
    fiscal_impact_statements: FiscalImpactStatement = Relationship(back_populates="bill_stage")

class BillAction(DBModelBase, table=True):
    bill_action_id: int = SQLModelField(primary_key=True)
    chamber: str
    description: str
    comment: Optional[str] = None
    date: Optional[date] = SQLModelField(
        default_factory=lambda x: datetime.strptime(x, "%m/%d/%Y").date() if x else None)
    time: Optional[time] = SQLModelField(
        default_factory=lambda x: datetime.strptime(x, "%H:%M").strftime("%I:%M %p") if x else None)
    journal_page: Optional[str] = None
    url: Optional[HttpUrl] = None

class Amendment(DBModelBase, table=True):
    amendment_id: int = SQLModelField(primary_key=True)
    reading: str
    number: str
    author: str
    coauthors: Optional[str] = None
    amendment_type: str
    action: str
    action_date: str
    html_link: Optional[str] = None
    pdf_link: Optional[str] = None


class BillDetail(DBModelBase, table=True):
    bill_url: str = SQLModelField(primary_key=True)
    bill_number: str
    caption_version: Optional[str] = None
    caption_text: Optional[str] = None
    last_action_dt: Optional[str] = None
    action_list: Optional[pd.DataFrame] = None
    stages: Optional[Dict[str, BillStage]] = SQLModelField(default_factory=dict)
    amendments: Optional[list[Amendment]] = None
    additional_documents: Optional[Dict[str, DocumentVersionLink]] = None
    house_committee: Optional[CommitteeDetails] = None
    house_committee_status: Optional[Dict[str, CommitteeBillStatus]] = None
    senate_committee: Optional[CommitteeDetails] = None
    senate_committee_status: Optional[Dict[str, CommitteeBillStatus]] = None



class BillList(DBModelBase, table=True):
    bill_list_id: str = SQLModelField(primary_key=True)
    chamber: ChamberTuple
    legislative_session: str
    committees: ClassVar[Dict[str, CommitteeDetails]] = {}
    bills: Optional[Dict[str, BillDetail]] = PydanticField(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        self.bill_list_id = self._generate_id()
    
    def __hash__(self):
        return hash(self.bill_list_id)

    def _generate_id(self):
        return f"{self.legislative_session}_{self.chamber.full}"

    # Move this method elsewhere or inject the interface
    def create_bill_list(self):
        with logfire_context("BillList.create_bill_list"):
            from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
            self.bills = BillListInterface._build_bill_list(chamber=self.chamber, lege_session=self.legislative_session)

    def create_bill_details(self):
        from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        with logfire_context("BillList.create_bill_details"):
            self.bills = BillListInterface._build_bill_details(
                bills=self.bills,
                chamber=self.chamber,
                committees=self.committees
                )