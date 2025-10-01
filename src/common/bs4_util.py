from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Tag


def get_value_or_none(tag: Optional[Tag]) -> Optional[str]:
    """
    tag에서 값 추출 or None
    :param tag:
    :return:
    """
    return tag.get_text(strip=True) if tag else None


def parse_html_to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")