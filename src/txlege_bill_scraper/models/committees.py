
from sqlmodel import Field as SQLModelField, Relationship

from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.bases import DBModelBase, NonDBModelBase


class CommitteeDetails(DBModelBase):
    name: str = SQLModelField(primary_key=True)
    chamber: ChamberTuple
    committee_bills: list["BillDetail"] = Relationship(back_populates="committee")

    def __repr__(self):
        return f"{self.name} Committee for the {self.chamber} Chamber"

class CommitteeBillStatus(DBModelBase):
    status: str
    vote: "CommitteeVoteCount" = Relationship(back_populates="vote")

class CommitteeVoteCount(DBModelBase):
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0