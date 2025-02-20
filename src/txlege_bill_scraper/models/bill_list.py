# from typing import Optional
#
# from sqlmodel import JSON, Relationship, SQLModel
# from sqlmodel import Field as SQLModelField
#
# from txlege_bill_scraper.interfaces.bill_list import BillListInterface
#
#
# # TODO: Rework this so that it's nested under the interface and use super() to call the interface methods
# class BillList(SQLModel):
#     bill_list_id: Optional[str] = SQLModelField(primary_key=True)
#     chamber: "ChamberTuple" = SQLModelField(sa_type=JSON)
#     legislative_session: str = SQLModelField()
#     committees: list["CommitteeDetails"] = Relationship(back_populates="bill_list")
#     bills: dict[str, dict[str, str]] = SQLModelField(default_factory=dict)
#
#     def __init__(self, **data):
#         super().__init__(**data)
#         self.bill_list_id = self._generate_id()
#
#     def __hash__(self):
#         return hash(self.bill_list_id)
#
#     def _generate_id(self):
#         return f"{self.legislative_session}_{self.chamber.full}"
#
#     # Move this method elsewhere or inject the interface
#     def create_bill_list(self):
#         # from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
#         self.bills = BillListInterface.build_bill_list(
#             chamber=self.chamber,
#             lege_session=self.legislative_session,
#             bill_list_id=self.bill_list_id,
#         )
#
#     def create_bill_details(self):
#         # from src.txlege_bill_scraper.navigator import BillListInterface  # Local import
#         self.bills = BillListInterface.build_bill_details(
#             _bill_list_id=self.bill_list_id,
#             _bills=self.bills,
#             _chamber=self.chamber,
#             _committees=self.committees,
#         )
