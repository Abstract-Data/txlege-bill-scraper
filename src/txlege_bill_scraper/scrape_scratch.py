from __future__ import annotations

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

OPTIONS = ChromeOptions()
OPTIONS.add_argument("--window-size=1920,1080")
OPTIONS.page_load_strategy = "none"

DRIVER = webdriver.Chrome(options=OPTIONS)
WAIT = WebDriverWait(DRIVER, 10)

DRIVER.get('http://capitol.texas.gov/BillLookup/Text.aspx?LegSess=87R&Bill=HB30')

# TODO: Need to format get_links func to handle the element being a list, and if so merge the results into a single dict, otherwise return a single dict
def get_links(element) -> dict:
    return {
        'pdf': element.get_attribute("href") if ".pdf" in element.get_attribute("href") else None,
        'txt': element.get_attribute("href") if ".htm" in element.get_attribute("href") else None,
        'word_doc': element.get_attribute("href") if ".doc" in element.get_attribute("href") else None,
    }

rows = iter(DRIVER.find_elements(By.CSS_SELECTOR, "tr:not(:first-child)")[1:])
version_lines = next(rows)
version = version_lines.text

bill_links = version_lines.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
fiscal_note = version_lines.find_elements(By.CSS_SELECTOR, "td:nth-child(3) a")
analysis = version_lines.find_elements(By.CSS_SELECTOR, "td:nth-child(4) a")
witness_list = version_lines.find_elements(By.CSS_SELECTOR, "td:nth-child(5) a")
summary = version_lines.find_elements(By.CSS_SELECTOR, "td:nth-child(6) a")
link_dict = {}
link_dict['bill_links'] = get_links(bill_links)
link_dict['fiscal_note1'] = {get_links(x) for x in fiscal_note if isinstance(fiscal_note, list)}

link_dict['fiscal_note2'] = get_links(fiscal_note[1])
link_dict['analysis'] = get_links(analysis)
link_dict['witness_list'] = get_links(witness_list)
link_dict['summary'] = get_links(summary)

while True:
    try:
        each_version = next(version_lines)
        if not each_version.text:
            break
        version_dict[each_version.text] = None

        bill_links = each_version.find_elements(By.CSS_SELECTOR, "td:nth-child(2) a")
        fiscal_note = each_version.find_elements(By.CSS_SELECTOR, "td:nth-child(3) a")
        analysis = each_version.find_elements(By.CSS_SELECTOR, "td:nth-child(4) a")
        witness_list = each_version.find_elements(By.CSS_SELECTOR, "td:nth-child(5) a")
        summary = each_version.find_elements(By.CSS_SELECTOR, "td:nth-child(6) a")

        def get_links(element) -> dict:
            for _link in element:
                return {
                    'pdf': next((x.text for x in _link if "pdf" in x.get_attribute('href')), None),
                    'txt': next((x.text for x in _link if "htm" in x.get_attribute('href')), None),
                    'word_doc': next((x.text for x in _link if "doc" in x.get_attribute('href')), None),
                }

        version_dict[each_version.text] = {
            'bill_links': get_links(bill_links)
        }
        # for link in fiscal_note:
        #     version_dict[each_version.text].update(
        #         {'fiscal_note': next((x.text for x in link.get_attribute('href') if "pdf" in x.text), None)}
        #     )

    except StopIteration:
        break
    _links = each_version.find_elements(By.CSS_SELECTOR, f"td:nth-child(2) a")
    _dict['pdf'] = {x.text: x.get_attribute('href') for x in _links if "pdf" in x.text}
    _dict['txt'] = {x.text: x.get_attribute('href') for x in _links if "htm" in x.text}
    _dict['word_doc'] = {x.text: x.get_attribute('href') for x in _links if "doc" in x.text}
    version_dict[_dict['version']] = _dict

version_lines = iter(
    zip(
        rows[1].find_elements(By.CSS_SELECTOR, "td"),
        (rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(2) a"), None),
        (rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(3) a") None),
        (rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(4) a"), None),
        (rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(5) a"), None),
        (rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(6) a"), None)
    ))
version, bill_links, fiscal_note, analysis, witness_list, summary = next(version_lines)
# for version, links in version_lines:
#     print(version.text.strip())
#     print(links.get_attribute('href'))
version = rows[1].find_element(By.CSS_SELECTOR, "td:first-child").text.strip()
links = rows[1].find_elements(By.CSS_SELECTOR, "td:nth-child(2) a")