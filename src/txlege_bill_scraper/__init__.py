import inject
from driver import BuildWebDriver

def configure_dependencies(binder: inject.Binder) -> None:
    binder.bind(BuildWebDriver, BuildWebDriver())

inject.configure(configure_dependencies)

def main() -> None:
    print("Hello from txlege-bill-scraper!")
