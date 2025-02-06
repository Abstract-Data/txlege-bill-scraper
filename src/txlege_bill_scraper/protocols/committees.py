# from typing import Protocol, Optional, List, Dict
# import pandas as pd
# from pydantic import HttpUrl
# from datetime import datetime, date, time
#
#
# class CommitteeDetailsProtocol(Protocol):
#     name: str
#     chamber: "ChamberTuple"
#     committee_bills: List["BillDetailProtocol"] = []
#
#     def __repr__(self):
#         return f"{self.name} Committee for the {self.chamber} Chamber"
#
#     def __hash__(self):
#         return hash(self.chamber + self.name)
#
#
# class CommitteeVoteCountProtocol(Protocol):
#     committee_bill_vote_id: str
#     ayes: int = 0
#     nays: int = 0
#     present_not_voting: int = 0
#     absent: int = 0
#
# class CommitteeBillStatusProtocol(Protocol):
#     committee_bill_num: str
#     status: str
#     vote: CommitteeVoteCountProtocol = None