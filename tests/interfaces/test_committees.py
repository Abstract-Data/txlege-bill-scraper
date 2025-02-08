from hypothesis import given
from hypothesis import strategies as st

from txlege_bill_scraper.interfaces.committees import CommitteeInterface


@given(st.builds(tuple, st.text(), st.text()))
def test_get_committee_details(committee):
    result = CommitteeInterface._get_committee_details(committee)
    assert isinstance(result, dict)
    assert "committee" in result
    assert "chamber" in result


def test_get_committee_list():
    result = CommitteeInterface._get_committee_list()
    assert isinstance(result, list)
    assert all(isinstance(committee, tuple) for committee in result)
    assert all(len(committee) == 2 for committee in result)
