import unittest
from hypothesis.stateful import Bundle, RuleBasedStateMachine, rule

from txlege_bill_scraper.interfaces import SessionInterface
from txlege_bill_scraper.protocols import HOUSE


class SessionInterfaceTest(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.chamber = HOUSE
        self.legislative_session = "88"
        self.session = SessionInterface(
            chamber=self.chamber, legislative_session=self.legislative_session
        )
