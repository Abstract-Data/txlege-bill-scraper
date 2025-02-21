import functools
from typing import Optional, List, Dict, Any
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
from datetime import datetime
import string
from urllib.parse import parse_qs, urlparse

from urllib.parse import urljoin
import httpx
import asyncio

from driver import BuildWebDriver, WebDriver
from interfaces.link_builders.bases import LegislativeSessionLinkBuilder

# driver = BuildWebDriver()
# driver.build()
# DRIVER_AND_WAIT = driver.driver_and_wait(_driver=BuildWebDriver.DRIVER, _wait=BuildWebDriver.WAIT)
base_url = 'https://capitol.texas.gov'
test_url = "https://capitol.texas.gov/BillLookup/Actions.aspx?LegSess=87R&Bill=HB2"
member_test = {
    'name': 'test_name',
    'member_url': test_url
}
response = httpx.get(test_url)
soup = BeautifulSoup(response.text, 'html.parser')
tables = soup.find_all("form")[1]
actions_table = tables.find_all("table")[1]
rows = actions_table.find_all("tr")[1:]
row_data = {}
for row in rows:
    cells = row.find_all("td")
    if len(cells) >= 3:
        _data = {
            'tier': cells[0].text.strip(),
            'description': cells[1].text.strip(),
            'description_url': urljoin(base_url, cells[1].find("a").get("href")) if cells[1].find("a") else None,
            'comment': cells[2].text.strip() if cells[2].text.strip() else None,
            'date': datetime.strptime(cells[3].text.strip(), '%m/%d/%Y').date() if len(cells) >= 4 and cells[
                3].text.strip() else None,
            'time': datetime.strptime(cells[4].text.strip(), "%I:%M %p").time() if len(cells) >= 5 and cells[
                4].text.strip() else None,
            'journal_page': cells[5].text.strip() if len(cells) >= 6 and cells[5].text.strip() else None,
        }
        row_data[cells[0].text.strip()] = _data