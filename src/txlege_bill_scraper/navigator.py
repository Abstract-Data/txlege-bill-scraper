from pydantic import HttpUrl
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import undetected_chromedriver as uc
from pathlib import Path
from pydantic import HttpUrl


DOWNLOAD_PATH = Path.home() / 'Downloads'
BRAVE_PATH = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'

options = uc.ChromeOptions()
options.binary_location = str(BRAVE_PATH)
options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
# options.add_argument("start-maximized")  # ensure window is full-screen
options.page_load_strategy = "none"  # Load the page as soon as possible

driver = uc.Chrome(options=options)
driver.get("https://capitol.texas.gov/Home.aspx")
wait = WebDriverWait(driver, 10)
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House"))).click()
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "House Members"))).click()
wait.until(EC.presence_of_element_located((By.ID, "content"))).click()
member_list = driver.find_element(By.ID, "content")
links = member_list.find_elements(By.TAG_NAME, "a")
member_links = iter(x.get_attribute("href") for x in links)

driver.get(next(member_links))
wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Bills Authored")))
def get_link(value: str, by: By = By.LINK_TEXT) -> str:
    return driver.find_element(by, value).get_attribute('href')
url = "https://capitol.texas.gov/reports/report.aspx?LegSess={session}}&ID={bill_writer_type}&Code={member_id}"
member_name = driver.find_element(By.ID, "usrHeader_lblPageTitle").text
member_contact = driver.find_element(By.ID, "contactInfo")
member_district = member_contact.find_element(By.ID, "lblDistrict").text
member_capitol_office = member_contact.find_element(By.ID, "lblCapitolOffice").text
member_capitol_phone = member_contact.find_element(By.ID, "lblCapitolPhone").text
member_district_address1 = member_contact.find_element(By.ID, "lblDistrictAddress1").text
member_district_address2 = member_contact.find_element(By.ID, "lblDistrictAddress2").text
member_district_phone = member_contact.find_element(By.ID, "lblDistrictPhone").text
member_committee_assignments = driver.find_element(By.ID, "committeeAssignments")
bills_authored = get_link("Bills Authored")
bills_sponsored = get_link("Bills Sponsored")
bills_coauthored = get_link("Bills Coauthored")
bills_cosponsored = get_link("Bills Cosponsored")
amendments_authored = get_link("Amendments Authored")
member_homepage = get_link("Home Page", by=By.PARTIAL_LINK_TEXT)

driver.get(bills_authored)
bill_links = driver.find_elements(By.TAG_NAME, "table")
bill_link_urls = {
    " ".join(
        (x
        .text
        .split('\n')[0]
        .split()[:2])): (x
                         .find_element(By.TAG_NAME, "a")
                         .get_attribute("href")
                         )
    for x in bill_links}

url1 = next(iter(bill_link_urls.values()))
driver.get(url1)
actions = driver.find_element(By.ID, "Form1").text.split('\n')
find_where_actions_start = (i + 2 for i, x in enumerate(actions) if x.startswith("Actions:")).__next__()

t1 = ['Description', 'Comment', 'Date', 'Time', 'Journal Page']
action_list = []
for x in actions[find_where_actions_start:]:
    t2 = x.split()
    t3 = dict(zip(t1, t2))
    action_list.append(t3)

driver.find_element(By.LINK_TEXT, "Text").click()
_bill_version_table = driver.find_element(By.ID, "Form1")
_header = _bill_version_table.find_elements(By.TAG_NAME, "tr")[0]
_header_text = [x.text.replace('\n', ' ') for x in _header.find_elements(By.TAG_NAME, "td")]
bill_stages = []
for x in _bill_version_table.find_elements(By.TAG_NAME, "tr")[1:]:
    _bill_stage = dict(zip(_header_text, [y.text for y in x.find_elements(By.TAG_NAME, "td")]))
    bill_stages.append(_bill_stage)
# action_details = actions.find_element(By.ID, "Form1")
# driver.get(member_homepage)
# wait.until(EC.element_to_be_clickable((By.TAG_NAME, "h1")))
# member_name = driver.find_element(By.TAG_NAME, "h1").text
# member_address = next((x for x in driver.find_elements(By.TAG_NAME, "h4") if "Capitol Address" in x.text), None)
# member_address_str = member_address.find_element(By.XPATH, "./following-sibling::p").text.split("\n")
# member_counties_represented = next((x for x in driver.find_elements(By.TAG_NAME, "h4") if "Counties Represented" in x.text), None)
# member_counties_represented_str = member_counties_represented.find_element(By.XPATH, "./following-sibling::p").text.split("\n")
# member_committees_page = get_link("Committees")
# driver.get(member_committees_page)
# bill_authored_url = driver.find_element(By.LINK_TEXT, "Bills Authored").get_attribute("href")
# bill_page = driver.get(bill_authored_url)
# bill_links = driver.find_elements(By.TAG_NAME, "table")
# bill_link_urls = [x.find_element(By.TAG_NAME, "a").get_attribute("href") for x in bill_links]
# driver.get(bill_link_urls[0])
# wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "General Reports"))).click()
# wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Filed House Bills"))).click()
# driver.implicitly_wait(5)
# wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
# wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, "table")))
# tables = driver.find_element(By.TAG_NAME, "body")
# bill_link_dict = [x for x in tables if x.find_elements(By.TAG_NAME, "a")]


# hb1 = [EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, x)) for x in bill_link_dict]

# for x in bill_link_dict:
#     wait.until(EC.element_to_be_clickable(x)).click()
#     wait.until(lambda d: x.is_displayed())
#     driver.implicitly_wait(5)
#     driver.back()