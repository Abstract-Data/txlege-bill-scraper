from unittest.mock import MagicMock, patch

from hypothesis import given
from hypothesis import strategies as st

from txlege_bill_scraper.interfaces import SessionInterface


@given(chamber=st.text(), legislative_session=st.one_of(st.text(), st.integers()))
def test_session_interface_init(chamber, legislative_session):
    session_interface = SessionInterface(
        chamber=chamber, legislative_session=legislative_session
    )
    assert session_interface.chamber == chamber
    assert session_interface.legislative_session == legislative_session


def test_navigate_to_page():
    with patch.object(
        SessionInterface, "driver_and_wait", return_value=(MagicMock(), MagicMock())
    ):
        session_interface = SessionInterface(chamber="House", legislative_session="89")
        session_interface.navigate_to_page()


def test_build_bill_list():
    with patch.object(
        SessionInterface, "driver_and_wait", return_value=(MagicMock(), MagicMock())
    ):
        session_interface = SessionInterface(chamber="House", legislative_session="89")
        session_interface.build_bill_list()


def test_build_member_list():
    with patch.object(
        SessionInterface, "driver_and_wait", return_value=(MagicMock(), MagicMock())
    ):
        session_interface = SessionInterface(chamber="House", legislative_session="89")
        session_interface.build_member_list()


def test_build_committee_list():
    with patch.object(
        SessionInterface, "driver_and_wait", return_value=(MagicMock(), MagicMock())
    ):
        session_interface = SessionInterface(chamber="House", legislative_session="89")
        session_interface.build_committee_list()
