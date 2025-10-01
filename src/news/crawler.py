from typing import List, Optional, TypeVar, Generic, Iterator
from urllib.parse import urlparse, parse_qs

import requests

from common.base import BaseResponse
from common.bs4_util import get_value_or_none, parse_html_to_soup
from common.date_util import parse_date

T = TypeVar("T", bound=BaseResponse)


class NaverNewsItem(BaseResponse):
    def __init__(self, title, content, marks, link, date, press):
        self.title = title
        self.content = content
        self.marks = marks
        self.link = link
        self.date = date
        self.press = press

    def to_dict(self):
        return {
            "title": self.title,
            "content": self.content,
            "marks": self.marks,
            "link": self.link,
            "date": self.date,
            "press": self.press
        }


class NaverNewsCrawler(Generic[T], Iterator[List[T]]):
    BASE_URL = "https://s.search.naver.com/p/newssearch/3/api/tab/more"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.5993.88 Safari/537.36"
        ),
        "Referer": "https://search.naver.com/search.naver",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }

    def __init__(self, query: str, ds: str, de: str,
        headers: dict = None):
        self.query = query
        self.ds = ds
        self.de = de
        self.headers = headers or self.headers
        self.next_url: Optional[str] = self.BASE_URL
        self.params = {
            "cluster_rank": "0",
            "ds": ds,
            "de": de,
            "query": query,
            "pd": "3",
            "photo": "0",
            "ssc": "tab.news.all",
            "sort": "0",
            "sm": "tab_smr",
            "nso": f"so:r,p:from{ds.replace('.', '')}to{de.replace('.', '')},a:all",
        }
        self.response_cls = NaverNewsItem

    def all(self):
        all_news: List[T] = []
        while self.next_url:
            news_page = self._fetch_next()
            all_news.extend(news_page)
        return all_news

    def __iter__(self):
        return self

    def __next__(self) -> List[T]:
        if not self.next_url:
            raise StopIteration
        return self._fetch_next()  # 한 페이지 뉴스 전체 반환

    def _fetch_next(self) -> List[T]:
        response = requests.get(self.next_url, params=self.params,
                                headers=self.headers)
        response.raise_for_status()
        data = response.json()

        # 다음 페이지 URL 갱신
        next_url_str = data.get('url')
        if next_url_str:
            parsed = urlparse(next_url_str)
            self.next_url = next_url_str
            self.params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        else:
            self.next_url = None

        return self._parse_news(data)

    def _parse_news(self, data) -> List[T]:
        htmls = [item['html'] for item in data.get('collection', [])]
        if not htmls:
            return []

        soup = parse_html_to_soup("".join(htmls))
        news_item_tab = soup.select_one('.fds-news-item-list-tab')
        if not news_item_tab:
            return []

        items = news_item_tab.select('div.UD3s7I8expz3WkwQ004B')
        news_list: List[T] = []

        for news_item in items:
            title_tag = news_item.select_one(
                "a[data-heatmap-target='.tit'] span.sds-comps-text")
            body_tag = news_item.select_one(
                "a[data-heatmap-target='.body'] span.sds-comps-text")
            mark_tags = news_item.select(
                "a[data-heatmap-target='.body'] span.sds-comps-text mark")
            link_tag = news_item.select_one("a[data-heatmap-target='.tit']")
            date_tag = news_item.select_one(
                "span.sds-comps-profile-info-subtext span.sds-comps-text")
            press_tag = news_item.select_one(
                "div.sds-comps-profile-info-title span.sds-comps-text a span.sds-comps-text"
            )

            item = self.response_cls(
                title=get_value_or_none(title_tag),
                content=get_value_or_none(body_tag),
                marks=[get_value_or_none(m) for m in mark_tags],
                link=get_value_or_none(link_tag),
                date=parse_date(get_value_or_none(date_tag)),
                press=get_value_or_none(press_tag)
            )
            news_list.append(item)

        return news_list
