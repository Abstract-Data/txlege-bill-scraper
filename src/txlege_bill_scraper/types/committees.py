from __future__ import annotations
from typing import Protocol, Optional, List, Dict
import pandas as pd
from pydantic import HttpUrl
from datetime import datetime, date, time

from src.txlege_bill_scraper.types import ChamberTuple
from src.txlege_bill_scraper.types.bills import BillDetailProtocol


class CommitteeDetails(Protocol):
    name: str
    chamber: ChamberTuple
    committee_bills: List[BillDetailProtocol] = []

    def __repr__(self):
        return f"{self.name} Committee for the {self.chamber} Chamber"
    
    def __hash__(self):
        return hash(self.chamber + self.name)

class CommitteeBillStatusProtocol(Protocol):
    status: str
    vote: CommitteeVoteCountProtocol = None

class CommitteeVoteCountProtocol(Protocol):
    ayes: int = 0
    nays: int = 0
    present_not_voting: int = 0
    absent: int = 0