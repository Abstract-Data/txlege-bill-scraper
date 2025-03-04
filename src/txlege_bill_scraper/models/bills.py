from __future__ import annotations

from typing import Optional, Union
from sqlmodel import Field as SQLModelField, Relationship, JSON, SQLModel, Date, Time, ARRAY
from .bases import TexasLegislatureModelBase
from sqlmodel import Field as SQLModelField, String as SQLModelString, Date as SQLModelDate
from pydantic import  model_validator
from datetime import datetime, date

from protocols import BillDocFileType, BillDocDescription, WebElementDate, HttpsValidatedURL, WebElementText
from .committees import CommitteeDetails, CommitteeVote, CommitteeBill



class BillDocBase(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    bill_id: Optional[str] = SQLModelField(foreign_key="txlegebill.id")
    version_id: Optional[str] = SQLModelField(default=None, foreign_key="billversion.id")
    amendment_id: Optional[str] = SQLModelField(default=None, foreign_key="billamendment.id")
    version: Optional[str] = None
    doc_url: HttpsValidatedURL = SQLModelField(default=None, sa_type=SQLModelString)
    doc_type: Optional[BillDocFileType] = None
    doc_description: BillDocDescription

    @model_validator(mode="after")
    def create_id(self):
        self.id = f"{self.version_id}-{self.doc_description}-{self.doc_type}"
        return self

class BillDoc(BillDocBase):
    pass



class BillCompanion(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    bill_id: Optional[str] = SQLModelField(foreign_key="txlegebill.id")
    companion_url: HttpsValidatedURL = SQLModelField(sa_type=SQLModelString)
    companion_session_id: Optional[str] = None
    companion_bill_number: Optional[str] = None

    @model_validator(mode="after")
    def create_id(self):
        self.id = f"{self.bill_id}-Companion-{self.companion_bill_number}"
        return self


class BillAmendment(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    bill_id: Optional[str] = SQLModelField(foreign_key="txlegebill.id")
    chamber: Optional[str] = None
    author: Optional[str] = None
    reading: Optional[str] = None
    number: Optional[str] = None
    type_: Optional[str] = None
    action: Optional[str] = None
    action_date: WebElementDate = SQLModelField(default=None, sa_type=SQLModelDate)
    # docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    co_authors: Optional[Union[str, list, None]] = SQLModelField(default=None, sa_type=ARRAY(SQLModelString))

    @model_validator(mode="after")
    def create_id(self):
        hashed_data = super().create_hash(
            self.bill_id, self.number, self.type_, self.action_date
        )
        self.id = f"{self.bill_id}-Amendment-{hashed_data}"
        return self


class BillVersion(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    bill_id: Optional[str] = SQLModelField(foreign_key="txlegebill.id")
    version: Optional[str]

    # bill_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    # fiscal_note_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    # analysis_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    # witness_list_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    # committee_summary_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    # fiscal_impact_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    @model_validator(mode="after")
    def create_id(self):
        self.id = f"{self.bill_id}-Version-{self.version}"
        return self


class BillAction(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    bill_id: Optional[str] = SQLModelField(foreign_key="txlegebill.id")
    tier: str
    description: str
    description_url: HttpsValidatedURL = SQLModelField(sa_type=SQLModelString)
    comment: Optional[str] = None
    action_date: Optional[date] = SQLModelField(default=None, sa_type=Date)
    action_time: Optional[Time] = SQLModelField(default=None, sa_type=Time)
    journal_page: Optional[str] = None

    @model_validator(mode="after")
    def create_id(self):
        hashed_data = super().create_hash(
            self.bill_id,
            self.tier,
            self.description,
            self.action_date,
            self.action_time,
        )
        self.id = f"{self.bill_id}-Action-{hashed_data}"
        return self


class TXLegeBill(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    legislative_session: Optional[str] = None
    bill_number: Optional[str] = None
    bill_url: HttpsValidatedURL = SQLModelField(default=None, sa_type=SQLModelString)
    last_action_dt: WebElementDate = SQLModelField(default=None, sa_type=SQLModelDate)
    caption_version: WebElementText = SQLModelField(default=None, sa_type=SQLModelString)
    caption_text: WebElementText = SQLModelField(default=None, sa_type=SQLModelString)
    authors: WebElementText = SQLModelField(default=None, sa_type=SQLModelString)
    sponsors: WebElementText = SQLModelField(default=None, sa_type=SQLModelString)
    subjects: Optional[list[Union[str]]] = SQLModelField(default=None, sa_type=ARRAY(SQLModelString))
    # versions: Optional[Dict[str, BillVersion]] = SQLModelField(default_factory=dict)
    # amendments: Optional[List[BillAmendment]] = SQLModelField(default_factory=list)
    # companions: List[BillCompanion] = SQLModelField(default_factory=list)
    # committees: List[str] = SQLModelField(default_factory=list)
    # actions: List[BillAction] = SQLModelField(default_factory=list)

    @model_validator(mode="after")
    def create_ids(self):
        self.id = f"{self.legislative_session}-{self.bill_number}"
        return self
