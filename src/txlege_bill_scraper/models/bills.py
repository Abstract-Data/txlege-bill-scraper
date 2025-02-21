from typing import Optional, Annotated, Dict, Any, List
from enum import Enum
from sqlmodel import Field as SQLModelField, Relationship, JSON, SQLModel, Date, Time
from .bases import TexasLegislatureModelBase
from sqlmodel import Field as SQLModelField
from pydantic import HttpUrl, AfterValidator, BeforeValidator, PastDate, model_validator
from bs4 import Tag
import re
from datetime import datetime, date

from txlege_bill_scraper.protocols import BillDocFileType, BillDocDescription
from txlege_bill_scraper.build_logger import LogFireLogger
from .committees import CommitteeDetails, CommitteeVote

def get_element_text(element: Any) -> str | list | None:
    if element:
        if isinstance(element, Tag):
            result = element.text.strip()
            result_list = result.split('|')
            if len(result_list) > 1:
                return [x.strip() for x in result_list]
            return result
        return element.strip()
    return None

def format_datetime(element: Any) -> date | None:
    if not element:
        return None
    field_text = get_element_text(element)
    date_match = re.compile(r'\d{2}/\d{2}/\d{4}').search(field_text)
    return datetime.strptime(date_match.group(), "%m/%d/%Y").date() if date_match else None

def check_url(value: HttpUrl) -> HttpUrl:
    if not value or value.scheme == 'https':
        pass
    else:
        value = HttpUrl(value.__str__().replace("http://", "https://"))
    return value


HttpsValidatedURL = Annotated[Optional[HttpUrl], AfterValidator(check_url)]
WebElementText = Annotated[Optional[str | list], BeforeValidator(get_element_text)]
WebElementDate = Annotated[Optional[PastDate], BeforeValidator(format_datetime)]

class BillDoc(TexasLegislatureModelBase):
    doc_id: Optional[str] = None
    version: Optional[str] = None
    doc_url: HttpsValidatedURL = None
    doc_type: Optional[BillDocFileType] = None
    doc_description: BillDocDescription

class BillCompanion(TexasLegislatureModelBase):
    bill_number: Optional[str] = None
    companion_url: HttpsValidatedURL = None
    companion_session_id: Optional[str] = None
    companion_bill_number: Optional[str] = None

class BillAmendment(TexasLegislatureModelBase):
    amendment_id: Optional[str] = None
    bill_number: Optional[str] = None
    chamber: Optional[str] = None
    reading: Optional[str] = None
    number: Optional[str] = None
    type_: Optional[str] = None
    action: Optional[str] = None
    action_date: WebElementDate = None
    docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    co_authors: Optional[str | list] = None

class BillVersion(TexasLegislatureModelBase):
    bill_version_id: Optional[str] = None
    bill_number: Optional[str] = None
    version: Optional[str] = None
    bill_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    fiscal_note_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    analysis_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    witness_list_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    committee_summary_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)
    fiscal_impact_docs: Optional[list[BillDoc]] = SQLModelField(default_factory=list)

class BillAction(TexasLegislatureModelBase):
    bill_id: Optional[str] = None
    tier: str
    description: str
    description_url: Optional[HttpsValidatedURL] = None
    comment: Optional[str] = None
    action_date: Optional[date] = None
    action_time: Optional[Time] = None
    journal_page: Optional[str] = None

class TXLegeBill(TexasLegislatureModelBase):
    bill_id: Optional[str] = None
    legislative_session: Optional[str] = None
    bill_number: Optional[str] = None
    bill_url: HttpsValidatedURL = None
    last_action_dt: WebElementDate = None
    caption_version: WebElementText = None
    caption_text: WebElementText = None
    authors: WebElementText = None
    sponsors: WebElementText = None
    subjects: Optional[List[str]] = None
    versions: Optional[Dict[str, BillVersion]] = SQLModelField(default_factory=dict)
    amendments: Optional[List[BillAmendment]] = SQLModelField(default_factory=list)
    companions: List[BillCompanion] = SQLModelField(default_factory=list)
    committees: List[str] = SQLModelField(default_factory=list)
    actions: List[BillAction] = SQLModelField(default_factory=list)

    def create_ids(self):
        self.bill_id = f"{self.legislative_session}-{self.bill_number}"
        for version in self.versions.values():
            version.bill_version_id = f"{self.bill_id}-{version.version}"
            version.bill_number = self.bill_number
            for doc in version.bill_docs:
                doc.doc_id = f"{version.bill_version_id}-{doc.doc_description}-{doc.doc_type}"
        for amendment in self.amendments:
            amendment.amendment_id = f"{self.bill_id}-{amendment.number}"
            amendment.bill_number = self.bill_number
            for doc in amendment.docs:
                doc.doc_id = f"{amendment.amendment_id}-{doc.doc_description}-{doc.doc_type}"
        return self


#
# class DocumentVersionLink(DBModelBase, table=True):
#     document_id: int = SQLModelField(primary_key=True)
#     bill_number: Optional[str] = SQLModelField(foreign_key="billdetail.bill_number", default=None)
#     bill_stage_id: Optional[int] = SQLModelField(foreign_key="billstage.bill_stage_id")
#     fiscal_impact_id: Optional[int] = SQLModelField(foreign_key="fiscalimpactstatement.fiscal_impact_statement_id", default=None)
#     document_type: DocumentType
#     pdf: Optional[str] = SQLModelField(default=None)
#     txt: Optional[str] = SQLModelField(default=None)
#     word_doc: Optional[str] = SQLModelField(default=None)
#     bill: Optional["BillDetail"] = Relationship(back_populates="additional_documents")
#     bill_stage: "BillStage" = Relationship(back_populates="documents")
#     fiscal_impact_statement: Optional["FiscalImpactStatement"] = Relationship(back_populates="documents")
#
# class FiscalImpactStatement(DBModelBase, table=True):
#     fiscal_impact_statement_id: int = SQLModelField(primary_key=True)
#     version: str
#     released_by: str
#     documents: list["DocumentVersionLink"] = Relationship(
#         back_populates="fiscal_impact_statement",
#         sa_relationship_kwargs= {
#             "primaryjoin":
#                 "and_(FiscalImpactStatement.fiscal_impact_statement_id==DocumentVersionLink.fiscal_impact_id, "
#                           "DocumentVersionLink.document_type=='fiscal_impact')",
#             "lazy": "selectin"
#         }
#     )
#     bill_stage: Optional["BillStage"] = Relationship(back_populates="fiscal_impact_statements")
#
# class BillStage(DBModelBase, table=True):
#     bill_stage_id: int = SQLModelField(primary_key=True)
#     bill_num: str = SQLModelField(foreign_key="billdetail.bill_number")
#     fiscal_impact_statements_id: Optional[int] = SQLModelField(
#         default=None,
#         foreign_key="fiscalimpactstatement.fiscal_impact_statement_id"
#     )
#     version: str
#     documents: list[DocumentVersionLink] = Relationship(
#         back_populates="bill_stage",
#         sa_relationship_kwargs={"lazy": "selectin"}
#     )
#     fiscal_note: list[DocumentVersionLink] = Relationship(
#         back_populates="bill_stage",
#         sa_relationship_kwargs={
#             "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
#                          "DocumentVersionLink.document_type=='fiscal_note')",
#             "overlaps": "documents,analysis,witness_list,committee_summary"
#         }
#     )
#     analysis: list[DocumentVersionLink] = Relationship(
#         back_populates="bill_stage",
#         sa_relationship_kwargs={
#             "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
#                          "DocumentVersionLink.document_type=='analysis')",
#             "overlaps": "documents,fiscal_note,witness_list,committee_summary"
#         }
#     )
#     witness_list: list[DocumentVersionLink] = Relationship(
#         back_populates="bill_stage",
#         sa_relationship_kwargs={
#             "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
#                          "DocumentVersionLink.document_type=='witness_list')",
#             "overlaps": "documents,fiscal_note,analysis,committee_summary"
#         }
#     )
#     committee_summary: list[DocumentVersionLink] = Relationship(
#         back_populates="bill_stage",
#         sa_relationship_kwargs={
#             "primaryjoin": "and_(BillStage.bill_stage_id==DocumentVersionLink.bill_stage_id, "
#                          "DocumentVersionLink.document_type=='committee_summary')",
#             "overlaps": "documents,fiscal_note,analysis,witness_list"
#         }
#     )
#     fiscal_impact_statements: list["FiscalImpactStatement"] = Relationship(back_populates="bill_stage")
#     bill: Optional["BillDetail"] = Relationship(back_populates="stages")
#
# class BillAction(DBModelBase, table=True):
#     bill_action_id: int = SQLModelField(primary_key=True)
#     chamber: str
#     description: str
#     comment: Optional[str] = SQLModelField(default=None)
#     date: Optional[Date] = SQLModelField(default=None, sa_type=Date)
#     # date: Optional[date] = SQLModelField(
#     #     default_factory=lambda x: datetime.strptime(x, "%m/%d/%Y").date() if x else None)
#     time: Optional[Time] = SQLModelField(default=None, sa_type=Time)
#     # time: Optional[time] = SQLModelField(
#     #     default_factory=lambda x: datetime.strptime(x, "%H:%M").strftime("%I:%M %p") if x else None)
#     journal_page: Optional[str] = SQLModelField(default=None)
#     url: Optional[str] = SQLModelField(default=None)
#
# class Amendment(DBModelBase, table=True):
#     amendment_id: int = SQLModelField(primary_key=True)
#     bill_num: str = SQLModelField(foreign_key="billdetail.bill_number")
#     reading: str
#     number: str
#     author: str
#     coauthors: Optional[str] = SQLModelField(default=None)
#     amendment_type: str
#     action: str
#     action_date: str
#     html_link: Optional[str] = SQLModelField(default=None)
#     pdf_link: Optional[str] = SQLModelField(default=None)
#     bill_detail: list["BillDetail"] = Relationship(back_populates="amendments")
#
#
# class BillDetail(DBModelBase, table=True):
#     bill_url: str = SQLModelField(primary_key=True)
#     bill_number: str
#     companion: Optional[str] = SQLModelField(default=None)
#     bill_list_id: Optional[str] = SQLModelField(default=None, foreign_key="billlist.bill_list_id")
#     author: str
#     sponsor: Optional[str] = SQLModelField(default=None)
#     caption_version: Optional[str] = SQLModelField(default=None)
#     caption_text: Optional[str] = SQLModelField(default=None)
#     last_action_dt: Optional[str] = SQLModelField(default=None)
#     subjects: list[str] = SQLModelField(default_factory=list, sa_type=JSON)
#     action_list: list = SQLModelField(default_factory=list, sa_type=JSON)
#     stages: list["BillStage"] = Relationship(back_populates="bill")
#     amendments: list["Amendment"] = Relationship(back_populates="bill_detail")
#     additional_documents: list["DocumentVersionLink"] = Relationship(
#         back_populates="bill",
#         sa_relationship_kwargs={
#             "primaryjoin": "and_(BillDetail.bill_number==DocumentVersionLink.bill_number, "
#                           "DocumentVersionLink.document_type=='additional_document')",
#             "lazy": "selectin"
#         }
#     )
#     committee_name: Optional[str] = SQLModelField(default=None, foreign_key="committeedetails.name")
#     committee: Optional["CommitteeDetails"] = Relationship(back_populates="committee_bills")
#     bill_list: Optional["BillList"] = Relationship(back_populates="bills")
