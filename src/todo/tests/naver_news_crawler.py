from typing import List, Optional
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


def get_value_or_none(tag):
    return tag.get_text(strip=True) if tag else None


class NewsItem:

    def __init__(self, title, body, marks, link, date, press):
        self.title = title
        self.body = body
        self.marks = marks
        self.link = link
        self.date = date
        self.press = press

    def to_dict(self):
        return {
            "제목": self.title,
            "본문": self.body,
            "강조된 언어": self.marks,
            "기사 링크": self.link,
            "작성일": self.date,
            "언론사": self.press
        }


def _parse_news(data) -> List[NewsItem]:
    htmls = [item['html'] for item in data.get('collection', [])]
    if not htmls:
        return []

    soup = BeautifulSoup("".join(htmls), "html.parser")
    news_item_tab = soup.select_one('.fds-news-item-list-tab')
    if not news_item_tab:
        return []

    items = news_item_tab.select('div.UD3s7I8expz3WkwQ004B')
    news_list = []

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

        news_list.append(
            NewsItem(
                title=get_value_or_none(title_tag),
                body=get_value_or_none(body_tag),
                marks=[get_value_or_none(m) for m in mark_tags],
                link=get_value_or_none(link_tag),
                date=get_value_or_none(date_tag),
                press=get_value_or_none(press_tag)
            )
        )
    return news_list


class NaverNewsCrawler:
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

    def __init__(self, query: str, ds: str, de: str, headers: dict = None):
        self.query = query
        self.ds = ds
        self.de = de
        self.headers = headers or self.headers
        self.next_url: Optional[str] = self.BASE_URL  # 처음에는 기본 URL
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

    def has_next(self) -> bool:
        return self.next_url is not None

    def next(self) -> List[NewsItem]:
        """다음 페이지 뉴스 가져오기, URL과 params는 Response에서 갱신"""
        if not self.next_url:
            return []

        response = requests.get(self.next_url, params=self.params,
                                headers=self.headers)
        response.raise_for_status()
        data = response.json()

        next_url_str = data.get('url')
        if next_url_str:
            parsed = urlparse(next_url_str)
            self.next_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            self.params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        else:
            self.next_url = None  # 다음 페이지 없으면 종료

        return _parse_news(data)
