from hypothesis import given
from hypothesis import strategies as st

from txlege_bill_scraper.factories.bills import (
    create_bill_detail,
    extract_basic_details,
)


@given(st.text(), st.text(), st.text())
def test_create_bill_detail(bill_list_id, bill_number, bill_url):
    result = create_bill_detail(bill_list_id, bill_number, bill_url)
    assert result.bill_list_id == bill_list_id
    assert result.bill_number == bill_number
    assert result.bill_url == bill_url


@given(
    st.builds(dict, bill_list_id=st.text(), bill_number=st.text(), bill_url=st.text())
)
def test_extract_basic_details(bill):
    result = extract_basic_details(bill["bill_list_id"], bill, None, [], None)
    assert result.bill_list_id == bill["bill_list_id"]
    assert result.bill_number == bill["bill_number"]
    assert result.bill_url == bill["bill_url"]
