from sqlmodel import JSON, Relationship
from sqlmodel import Field as SQLModelField
from typing import Dict, Optional, List

from .bases import TexasLegislatureModelBase
from txlege_bill_scraper.protocols import ChamberTuple


class CommitteeVote(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None)
    committee_id: str
    bill_id: str
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0

    def __init__(cls, **data):
        super().__init__(**data)
        cls.id = cls.create_id()

    def create_id(self):
        return f"{self.committee_id}-{self.bill_id}-vote"


class CommitteeDetails(TexasLegislatureModelBase):
    committee_id: Optional[str] = SQLModelField(default=None)
    committee_name: str = SQLModelField(primary_key=True)
    committee_chamber: str
    committee_bills: List[str] = SQLModelField(default_factory=list)
    committee_votes: Dict[str, CommitteeVote] = SQLModelField(
        default_factory=dict
    )
    committee_url: str = SQLModelField(default=None)

    def __hash__(self):
        return hash(self.committee_name)

    def __repr__(self):
        return (
            f"{self.committee_name} Committee for the {self.committee_chamber} Chamber"
        )


#
# class CommitteeBillStatus(DBModelBase, table=True):
#     committee_bill_num: str = SQLModelField(primary_key=True)
#     committee_name: str = SQLModelField(
#         foreign_key=f"{CommitteeDetails.__tablename__}.name"
#     )
#     status: str
#     vote: list["CommitteeVoteCount"] = Relationship(
#         back_populates="committee_bill_status"
#     )
#     committee: "CommitteeDetails" = Relationship(
#         back_populates="committee_bill_statuses"
#     )
