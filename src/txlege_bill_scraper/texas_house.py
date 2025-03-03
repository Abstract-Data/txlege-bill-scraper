from interfaces import SessionDetailInterface
from protocols import SessionDetails
from db import engine
from sqlmodel import SQLModel

# from legislator import LegislatorBase
from protocols import HOUSE

LEGISLATIVE_SESSION: SessionDetails = SessionDetails(
    lege_session="89", lege_session_desc="R"
)


house_bills = SessionDetailInterface(
    chamber=HOUSE, legislative_session=LEGISLATIVE_SESSION
)
# SQLModel.metadata.create_all(engine)
house_bills.links.fetch()
house_bills.fetch()
# amendments = [x for x in house_bills.links.bills.values() if x.amendments]
# test = house_bills.links.bills.get("HB1")
# co_authors = [x['amendment_coauthors'] for x in house_bills.links.bills.values() if x.get('amendment_coauthors')]
# test = next(house_bills.bills)

# models = [x.model_dump() for x in house_bills.bills.values()]
# TODO: Deal with BillDetails references in Bill Interface Module to avoid circular imports.
# house_bills.generate_bills()

# hb9 = BillDetail(bill_number='HB9', bill_url="https://capitol.texas.gov/BillLookup/History.aspx?LegSess=87R&Bill=HB9")
# create_bill_stages(bill=hb9, _driver=BrowserDriver, _wait=BrowserWait)
