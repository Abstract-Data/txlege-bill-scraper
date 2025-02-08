from txlege_bill_scraper.driver import BuildWebDriver


def test_build_webdriver():
    BuildWebDriver.build()
    assert BuildWebDriver.DRIVER is not None
    assert BuildWebDriver.WAIT is not None


def test_close_driver():
    BuildWebDriver.build()
    BuildWebDriver.close_driver(BuildWebDriver.DRIVER)
    assert BuildWebDriver.DRIVER.service.process is None
