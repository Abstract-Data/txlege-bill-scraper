from typing import Optional
from enum import Enum
from sqlmodel import Field as SQLModelField, Relationship, JSON, SQLModel, Date, Time
from ..bases import DBModelBase
from .committees import CommitteeDetails, CommitteeBillStatus, CommitteeVoteCount

class DocumentType(str, Enum):
    BILL = "bill"
    FISCAL_NOTE = "fiscal_note"
    ANALYSIS = "analysis"
    WITNESS_LIST = "witness_list"
    COMMITTEE_SUMMARY = "committee_summary"
    FISCAL_IMPACT = "fiscal_impact_statement"
    ADDITIONAL_DOCUMENT = "additional_document"

class DocumentVersionLink(DBModelBase, table=True):
    document_id: int = SQLModelField(primary_key=True)
    bill_number: Optional[str] = SQLModelField(foreign_key="billdetail.bill_number", default=None)
    bill_stage_id: Optional[int] = SQLModelField(foreign_key="billstage.bill_stage_id")
    fiscal_impact_id: Optional[int] = SQLModelField(foreign_key="fiscalimpactstatement.fiscal_impact_statement_id", default=None)
    document_type: DocumentType
    pdf: Optional[str] = SQLModelField(default=None)
    txt: Optional[str] = SQLModelField(default=None)
    word_doc: Optional[str] = SQLModelField(default=None)
    bill: Optional["BillDetail"] = Relationship(back_populates="additional_documents")
    bill_stage: "BillStage" = Relationship(back_populates="documents")
    fiscal_impact_statement: Optional["FiscalImpactStatement"] = Relationship(back_populates="documents")

class FiscalImpactStatement(DBModelBase, table=True):
    fiscal_impact_statement_id: int = SQLModelField(primary_key=True)
    version: str
    released_by: str
    documents: list["DocumentVersionLink"] = Relationship(
        back_populates="fiscal_impact_statement",
        sa_relationship_kwargs= {
            "primaryjoin":
                "and_(FiscalImpactStatement.fiscal_impact_statement_id==DocumentVersionLink.fiscal_impact_id, "
                          "DocumentVersionLink.document_type=='fiscal_impact')",
            "lazy": "selectin"
        }
    )
    bill_stage: Optional["BillStage"] = Relationship(back_populates="fiscal_impact_statements")

class BillStage(DBModelBase, table=True):
    bill_stage_id: int = SQLModelField(primary_key=True)
    bill_num: str = SQLModelField(foreign_key="billdetail.bill_number")
    fiscal_impact_statements_id: Optional[int] = SQLModelField(
        default=None,
        foreign_key="fiscalimpactstatement.fiscal_impact_statement_id"
    )
    version: str
    documents: list[DocumentVersionLink] = Relationship(
        back_populates="bill_stage",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    fiscal_note: list[DocumentVersionLink] = Relationship(
        back_populates="bill_stage",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
                         "DocumentVersionLink.document_type=='fiscal_note')",
            "overlaps": "documents,analysis,witness_list,committee_summary"
        }
    )
    analysis: list[DocumentVersionLink] = Relationship(
        back_populates="bill_stage",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
                         "DocumentVersionLink.document_type=='analysis')",
            "overlaps": "documents,fiscal_note,witness_list,committee_summary"
        }
    )
    witness_list: list[DocumentVersionLink] = Relationship(
        back_populates="bill_stage",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
                         "DocumentVersionLink.document_type=='witness_list')",
            "overlaps": "documents,fiscal_note,analysis,committee_summary"
        }
    )
    committee_summary: list[DocumentVersionLink] = Relationship(
        back_populates="bill_stage",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
                         "DocumentVersionLink.document_type=='committee_summary')",
            "overlaps": "documents,fiscal_note,analysis,witness_list"
        }
    )
    fiscal_impact_statements: list["FiscalImpactStatement"] = Relationship(back_populates="bill_stage")
    bill: Optional["BillDetail"] = Relationship(back_populates="stages")

class BillAction(DBModelBase, table=True):
    bill_action_id: int = SQLModelField(primary_key=True)
    chamber: str
    description: str
    comment: Optional[str] = SQLModelField(default=None)
    date: Optional[Date] = SQLModelField(default=None, sa_type=Date)
    # date: Optional[date] = SQLModelField(
    #     default_factory=lambda x: datetime.strptime(x, "%m/%d/%Y").date() if x else None)
    time: Optional[Time] = SQLModelField(default=None, sa_type=Time)
    # time: Optional[time] = SQLModelField(
    #     default_factory=lambda x: datetime.strptime(x, "%H:%M").strftime("%I:%M %p") if x else None)
    journal_page: Optional[str] = SQLModelField(default=None)
    url: Optional[str] = SQLModelField(default=None)

class Amendment(DBModelBase, table=True):
    amendment_id: int = SQLModelField(primary_key=True)
    bill_num: str = SQLModelField(foreign_key="billdetail.bill_number")
    reading: str
    number: str
    author: str
    coauthors: Optional[str] = SQLModelField(default=None)
    amendment_type: str
    action: str
    action_date: str
    html_link: Optional[str] = SQLModelField(default=None)
    pdf_link: Optional[str] = SQLModelField(default=None)
    bill_detail: list["BillDetail"] = Relationship(back_populates="amendments")


class BillDetail(DBModelBase, table=True):
    bill_url: str = SQLModelField(primary_key=True)
    bill_number: str
    companion: Optional[str] = SQLModelField(default=None)
    bill_list_id: Optional[str] = SQLModelField(default=None, foreign_key="billlist.bill_list_id")
    author: str
    sponsor: Optional[str] = SQLModelField(default=None)
    caption_version: Optional[str] = SQLModelField(default=None)
    caption_text: Optional[str] = SQLModelField(default=None)
    last_action_dt: Optional[str] = SQLModelField(default=None)
    subjects: list[str] = SQLModelField(default_factory=list, sa_type=JSON)
    action_list: list = SQLModelField(default_factory=list, sa_type=JSON)
    stages: list["BillStage"] = Relationship(back_populates="bill")
    amendments: list["Amendment"] = Relationship(back_populates="bill_detail")
    additional_documents: list["DocumentVersionLink"] = Relationship(
        back_populates="bill",
        sa_relationship_kwargs={
            "primaryjoin": "and_(BillDetail.bill_number==DocumentVersionLink.bill_number, "
                          "DocumentVersionLink.document_type=='additional_document')",
            "lazy": "selectin"
        }
    )
    committee_name: Optional[str] = SQLModelField(default=None, foreign_key="committeedetails.name")
    committee: Optional["CommitteeDetails"] = Relationship(back_populates="committee_bills")
    bill_list: Optional["BillList"] = Relationship(back_populates="bills")
