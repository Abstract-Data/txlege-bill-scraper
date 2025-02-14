from __future__ import annotations

from typing import List, Tuple, Dict, Any, Generator
from urllib.parse import parse_qs, urlparse
from icecream import ic

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

