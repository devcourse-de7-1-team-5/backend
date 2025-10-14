from typing import List, Tuple
from urllib.parse import urlparse, parse_qs

from common.base_async_crawler import BaseCrawler
from common.bs4_util import get_value_or_none, parse_html_to_soup
from common.date_util import parse_search_to_date
from common.next_url_setter import NextUrlSetter


class NaverNewsItem:
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


class NaverNextUrlSetter(NextUrlSetter):
    def get_next_url(self, current_url: str, current_params: dict,
        data: dict) -> Tuple[str | None, dict]:
        next_url_str = data.get('url')
        if next_url_str:
            parsed = urlparse(next_url_str)
            next_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            return next_url_str, next_params
        return None, current_params


class NaverNewsCrawler(BaseCrawler[NaverNewsItem]):
    BASE_URL = "https://s.search.naver.com/p/newssearch/3/api/tab/more"

    def __init__(self, query: str, ds: str, de: str, headers: dict = None, *,
        start: str = "0"):
        self.query = query
        self.ds = ds
        self.de = de

        params = {
            "cluster_rank": "0",
            "ds": ds,
            "de": de,
            "query": query,
            "pd": "3",
            "photo": "0",
            "ssc": "tab.news.all",
            "sort": "0",
            "sm": "tab_smr",
            "start": start,
            "nso": f"so:r,p:from{ds.replace('.', '')}to{de.replace('.', '')},a:all",
        }

        super().__init__(base_url=self.BASE_URL,
                         next_url_setter=NaverNextUrlSetter(),
                         headers=headers,
                         params=params)

    def _parse_data(self, data) -> List[NaverNewsItem]:
        next_url_str = data.get('url')
        if next_url_str:
            parsed = urlparse(next_url_str)
            self.next_url = next_url_str
            self.params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        else:
            self.next_url = None

        htmls = [item['html'] for item in data.get('collection', [])]
        if not htmls:
            return []

        soup = parse_html_to_soup("".join(htmls))
        news_item_tab = soup.select_one('.fds-news-item-list-tab')
        if not news_item_tab:
            return []

        items = news_item_tab.select('div.UD3s7I8expz3WkwQ004B')
        news_list: List[NaverNewsItem] = []

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

            news = NaverNewsItem(
                title=get_value_or_none(title_tag),
                content=get_value_or_none(body_tag),
                marks=[get_value_or_none(m) for m in mark_tags],
                link=link_tag.get('href') if link_tag else None,
                date=parse_search_to_date(get_value_or_none(date_tag)),
                press=get_value_or_none(press_tag)
            )
            news_list.append(news)

        return news_list
