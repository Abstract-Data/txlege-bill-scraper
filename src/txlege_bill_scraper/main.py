import pandas as pd
from pathlib import Path
from .texas_house import TxLegeLoader
#
house87 = TxLegeLoader("house")
house88 = TxLegeLoader("house", lege_session="88R")
senate88 = TxLegeLoader("senate", lege_session="88R")

# Get Bill captions f]or each
def get_bill_list(chamber: TxLegeLoader):
    bill_list = {}
    for member in chamber.members:
        for bill in chamber.members[member].legislation:
            bill_list[bill] = chamber.members[member].legislation[bill]
    return bill_list


# house_bills = pd.DataFrame.from_dict(
#     get_bill_list(
#         house88
#     ),
#     orient="index"
# ).to_csv(
#     Path.home() / 'Downloads' / 'house8R_bills.csv'
# )
#
# senate_bills = pd.DataFrame.from_dict(
#     get_bill_list(
#         senate88
#     ),
#     orient="index"
# ).to_csv(
#     Path.home() / 'Downloads' / 'senate88R_bills.csv'
# )