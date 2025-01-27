# factories/bill_factory.py
from src.txlege_bill_scraper.models.bills import BillDetail, BillStage, Amendment


def create_bill_detail(bill_number: str, bill_url: str) -> BillDetail:
    return BillDetail(bill_number=bill_number, bill_url=bill_url)

def create_bill_stage(_stage_dict: dict) -> BillStage:
    return BillStage(**_stage_dict)

def create_amendment(_amendment_dict: dict) -> Amendment:
    return Amendment(**_amendment_dict)
