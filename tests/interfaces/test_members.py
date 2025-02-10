import unittest
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from txlege_bill_scraper.interfaces.members import (
    MemberDetailInterface,
    MemberListInterface,
)
