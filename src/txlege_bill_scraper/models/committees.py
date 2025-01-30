from sqlmodel import Field as SQLModelField, Relationship, JSON
from ..bases import DBModelBase
from ..protocols import ChamberTuple


class CommitteeDetails(DBModelBase, table=True):
    name: str = SQLModelField(primary_key=True)
    chamber: ChamberTuple = SQLModelField(sa_type=JSON)
    bill_list_id: str = SQLModelField(foreign_key="billlist.bill_list_id")
    committee_bills: list["BillDetail"] = Relationship(
        back_populates="committee",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    committee_bill_statuses: list["CommitteeBillStatus"] = Relationship(
        back_populates="committee",
        sa_relationship_kwargs={"lazy": "selectin"}
    )
    bill_list: "BillList" = Relationship(back_populates="committees")

    def __repr__(self):
        return f"{self.name} Committee for the {self.chamber} Chamber"

class CommitteeBillStatus(DBModelBase, table=True):
    committee_bill_num: str = SQLModelField(primary_key=True)
    committee_name: str = SQLModelField(foreign_key=f"{CommitteeDetails.__tablename__}.name")
    status: str
    vote: list["CommitteeVoteCount"] = Relationship(back_populates="committee_bill_status")
    committee: "CommitteeDetails" = Relationship(back_populates="committee_bill_statuses")

class CommitteeVoteCount(DBModelBase, table=True):
    committee_bill_vote_id: str = SQLModelField(primary_key=True)
    committee_bill_num: str = SQLModelField(foreign_key="committeebillstatus.committee_bill_num")
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0
    committee_bill_status: CommitteeBillStatus = Relationship(back_populates="vote")
