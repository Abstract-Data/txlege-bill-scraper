from __future__ import annotations
from typing import Any
from datetime import datetime, date
from pydantic import HttpUrl
import re
from bs4 import Tag


def get_element_text(element: Any) -> str | list | None:
    if element:
        if isinstance(element, Tag):
            result = element.text.strip()
            result_list = result.split("|")
            if len(result_list) > 1:
                return [x.strip() for x in result_list]
            return result
        return element.strip()
    return None


def format_datetime(element: Any) -> date | None:
    if not element:
        return None
    field_text = get_element_text(element)
    date_match = re.compile(r"\d{2}/\d{2}/\d{4}").search(field_text)
    return (
        datetime.strptime(date_match.group(), "%m/%d/%Y").date() if date_match else None
    )


def check_url(value: HttpUrl) -> HttpUrl:
    if not value or value.scheme == "https":
        pass
    else:
        value = HttpUrl(value.__str__().replace("http://", "https://"))
    return value