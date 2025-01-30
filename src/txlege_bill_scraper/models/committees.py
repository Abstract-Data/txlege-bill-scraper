from sqlmodel import Field as SQLModelField, Relationship, JSON, SQLModel
from src.txlege_bill_scraper.protocols import ChamberTuple
from src.txlege_bill_scraper.bases import DBModelBase


class CommitteeDetails(SQLModel, table=True):
    name: str = SQLModelField(primary_key=True)
    chamber: ChamberTuple = SQLModelField(sa_type=JSON)
    committee_bills: list["BillDetail"] = Relationship(back_populates="committee")

    def __repr__(self):
        return f"{self.name} Committee for the {self.chamber} Chamber"

class CommitteeBillStatus(SQLModel, table=True):
    committee_bill_num: str = SQLModelField(primary_key=True)
    status: str
    vote: list["CommitteeVoteCount"] = Relationship(back_populates="vote")

class CommitteeVoteCount(SQLModel, table=True):
    committee_bill_vote_id: str = SQLModelField(primary_key=True)
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0
