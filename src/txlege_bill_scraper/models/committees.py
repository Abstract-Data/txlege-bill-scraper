from sqlmodel import JSON, Relationship
from sqlmodel import Field as SQLModelField
from typing import Dict, Optional, List
from pydantic import model_validator

from .bases import TexasLegislatureModelBase


class CommitteeDetails(TexasLegislatureModelBase):
    id: str
    committee_id: Optional[str] = SQLModelField(primary_key=True)
    committee_session_id: Optional[str] = SQLModelField(default=None)
    committee_name: str
    committee_chamber: str
    # committee_votes: Dict[str, CommitteeVote] = SQLModelField(
    #     default_factory=dict
    # )
    committee_url: str = SQLModelField(default=None)

    def __hash__(self):
        return hash(self.committee_name)

    def __repr__(self):
        return (
            f"{self.committee_name} Committee for the {self.committee_chamber} Chamber"
        )

class CommitteeBill(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    committee_id: str = SQLModelField(foreign_key="committeedetails.committee_id")
    bill_id: str = SQLModelField(foreign_key="txlegebill.bill_id")

    @model_validator(mode='after')
    def create_id(self):
        self.id = f"{self.committee_id}-{self.bill_id.split('-')[-1]}"
        return self

class CommitteeVote(TexasLegislatureModelBase):
    id: Optional[str] = SQLModelField(default=None, primary_key=True)
    committee_id: str = SQLModelField(foreign_key="committeedetails.committee_id")
    bill_id: str
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0

    @model_validator(mode='after')
    def create_id(self):
        self.id = f"{self.committee_id}-{self.bill_id.split('-')[-1]}-VOTE"
        return self
