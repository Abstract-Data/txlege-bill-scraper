from typing import Optional, Dict, ClassVar
from datetime import date, time
from sqlmodel import Field as SQLModelField, Relationship, JSON, SQLModel
from src.txlege_bill_scraper.build_logger import LogFireLogger
from src.txlege_bill_scraper.protocols import ChamberTuple
from src.txlege_bill_scraper.models.committees import CommitteeDetails, CommitteeBillStatus
from src.txlege_bill_scraper.navigator import BillListInterface 

logfire_context = LogFireLogger.logfire_context
class DocumentVersionLink(SQLModel, table=True):
    document_version_link_id: int = SQLModelField(primary_key=True)
    pdf: Optional[str] = SQLModelField(default=None)
    txt: Optional[str] = SQLModelField(default=None)
    word_doc: Optional[str] = SQLModelField(default=None)
    bill_stage: list["BillStage"] = Relationship(back_populates="bill")
    fiscal_impact_statements: list["FiscalImpactStatement"] = Relationship(back_populates="documents")

class FiscalImpactStatement(SQLModel, table=True):
    fiscal_impact_statement_id: int = SQLModelField(primary_key=True)
    version: str
    released_by: str
    documents: list["DocumentVersionLink"] = Relationship(back_populates="fiscal_impact_statements")

class BillStage(SQLModel, table=True):
    bill_stage_id: int = SQLModelField(primary_key=True)
    version: str
    bill: list["DocumentVersionLink"] = Relationship(back_populates="bill_stage")
    fiscal_note: list["DocumentVersionLink"] = Relationship(back_populates="bill_stage")
    analysis: list["DocumentVersionLink"] = Relationship(back_populates="bill_stage")
    witness_list: list["DocumentVersionLink"] = Relationship(back_populates="bill_stage")
    committee_summary: list["DocumentVersionLink"] = Relationship(back_populates="bill_stage")
    fiscal_impact_statements: list["FiscalImpactStatement"] = Relationship(back_populates="bill_stage")

class BillAction(SQLModel, table=True):
    bill_action_id: int = SQLModelField(primary_key=True)
    chamber: str
    description: str
    comment: Optional[str] = SQLModelField(default=None)
    date: Optional[date] = SQLModelField(default=None)
    # date: Optional[date] = SQLModelField(
    #     default_factory=lambda x: datetime.strptime(x, "%m/%d/%Y").date() if x else None)
    time: Optional[time] = SQLModelField(default=None)
    # time: Optional[time] = SQLModelField(
    #     default_factory=lambda x: datetime.strptime(x, "%H:%M").strftime("%I:%M %p") if x else None)
    journal_page: Optional[str] = SQLModelField(default=None)
    url: Optional[str] = None

class Amendment(SQLModel, table=True):
    amendment_id: int = SQLModelField(primary_key=True)
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


class BillDetail(SQLModel, table=True):
    bill_url: str = SQLModelField(primary_key=True)
    bill_number: str
    caption_version: Optional[str] = SQLModelField(default=None)
    caption_text: Optional[str] = SQLModelField(default=None)
    last_action_dt: Optional[str] = SQLModelField(default=None)
    action_list: Optional[list] = SQLModelField(default=None)
    stages: list["BillStage"] = SQLModelField(default_factory=dict)
    amendments: list["Amendment"] = Relationship(back_populates="bill_detail")
    additional_documents: list["DocumentVersionLink"] = None
    house_committee: list["CommitteeDetails"] = Relationship(back_populates="committee_bills")
    house_committee_status: list["CommitteeBillStatus"] = Relationship(back_populates="bill_detail")
    senate_committee: list["CommitteeDetails"] = Relationship(back_populates="committee_bills")
    senate_committee_status: list["CommitteeBillStatus"] = Relationship(back_populates="bill_detail")



class BillList(SQLModel, table=True):
    bill_list_id: Optional[str] = SQLModelField(primary_key=True)
    chamber: "ChamberTuple" = SQLModelField(sa_type=JSON)
    legislative_session: str = SQLModelField()
    committees: list["CommitteeDetails"] = Relationship(back_populates="bill_list")
    bills: list["BillDetail"] = Relationship(back_populates="bill_list")

    # def __init__(self, **data):
    #     super().__init__(**data)
    #     self.bill_list_id = self._generate_id()
    
    # def __hash__(self):
    #     return hash(self.bill_list_id)

    # def _generate_id(self):
    #     return f"{self.legislative_session}_{self.chamber.full}"

    # Move this method elsewhere or inject the interface
    def create_bill_list(self):
        with logfire_context("BillList.create_bill_list"):
            # from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
            self.bills = BillListInterface._build_bill_list(chamber=self.chamber, lege_session=self.legislative_session)

    def create_bill_details(self):
        # from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
        with logfire_context("BillList.create_bill_details"):
            self.bills = BillListInterface._build_bill_details(
                bills=self.bills,
                chamber=self.chamber,
                committees=self.committees
                )
