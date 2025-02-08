from txlege_bill_scraper.bases import InterfaceBase


def test_select_legislative_session():
    result = InterfaceBase.select_legislative_session()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_get_text_by_label():
    result = InterfaceBase._get_text_by_label("label", None)
    assert result is None
