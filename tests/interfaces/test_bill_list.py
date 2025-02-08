from hypothesis import given
from hypothesis import strategies as st

from txlege_bill_scraper.interfaces.bill_list import BillListInterface


@given(st.builds(tuple, st.text(), st.text()))
def test_extract_bill_link(bill):
    result = BillListInterface._extract_bill_link(bill)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_get_bill_links():
    result = BillListInterface._get_bill_links()
    assert isinstance(result, list)
    assert all(isinstance(bill, tuple) for bill in result)
    assert all(len(bill) == 2 for bill in result)
