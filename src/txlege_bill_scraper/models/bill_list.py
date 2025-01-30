from typing import Optional
from sqlmodel import Field as SQLModelField, Relationship, SQLModel, JSON
from ..build_logger import LogFireLogger
from ..navigator import BillListInterface

logfire_context = LogFireLogger.logfire_context

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
                bill_list_id=self.bill_list_id,
                bills=self.bills,
                chamber=self.chamber,
                committees=self.committees
                )