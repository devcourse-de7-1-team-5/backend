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

def get_image_src(tag: Optional[Tag]) -> Optional[str]:
    if tag:
        # tag 내에서 img 태그를 찾고, src 속성값을 가져옵니다.
        img_tag = tag.find('img')
        if img_tag:
            return img_tag.get('src')
    return None