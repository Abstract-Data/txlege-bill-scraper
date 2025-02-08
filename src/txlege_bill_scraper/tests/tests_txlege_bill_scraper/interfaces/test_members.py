import unittest

import hypothesis.strategies as st
import pytest
from hypothesis.stateful import RuleBasedStateMachine, rule, precondition

from src.txlege_bill_scraper.interfaces.members import MemberDetailInterface, MemberListInterface

class MemberDetailInterfaceTest(RuleBasedStateMachine):

    def __init__(self):
        super().__init__()
        self.member = None
        self.members = None