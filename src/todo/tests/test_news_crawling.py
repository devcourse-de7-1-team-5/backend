from typing import TypedDict, List
from xmlrpc.client import DateTime

import requests
from bs4 import BeautifulSoup
from django.test import TestCase
from requests import Response


class CollectionItemType(TypedDict):
    html: str
    script: str
    style: str


class ResponseDataType(TypedDict):
    collection: List[CollectionItemType]
    url: str  # URL for next page


def _get_response(drama_name: str, start_date: DateTime,
    end_date: str) -> Response:
    url = "https://search.naver.com/search.naver"

    params = {
        "ssc": "tab.news.all",
        "query": drama_name,
        "sm": "tab_opt",
        "sort": "0",
        "photo": "0",
        "field": "0",
        "pd": "3",
        "ds": start_date,
        "de": end_date,
        "docid": "",
        "related": "0",
        "mynews": "0",
        "office_type": "0",
        "office_section_code": "0",
        "news_office_checked": "",
        "nso": "so:r,p:from20230930to20250930",
        "is_sug_officeid": "0",
        "office_category": "0",
        "service_area": "0",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response


class TestNewsCrawling(TestCase):
    mock_dramas = ["폭군의 셰프", "대운을잡아라", "태양의후예"]
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

    def test_new_more(self):
        result = []
        url = "https://s.search.naver.com/p/newssearch/3/api/tab/more"
        start = 0
        ds = "2023.06.03"
        de = "2023.09.30"
        query = "태양의 후예"
        params = {
            "cluster_rank": "0",
            "ds": ds,  # start
            "de": de,  # end
            "query": query,  # 검색어
            "start": start,
            "pd": "3",
            "photo": "0",
            "ssc": "tab.news.all",
            "sort": "0",
            "sm": "tab_smr",
            "nso": "so:r,p:from20230603to20230930,a:all",
        }

        response: Response = requests.get(url, params=params,
                                          headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data: ResponseDataType = response.json()

        htmls = [item['html'] for item in data['collection']]

        soup = BeautifulSoup(*htmls, "html.parser")
        news_item_tab = soup.select_one('.fds-news-item-list-tab')
        news_items = news_item_tab.select('div.UD3s7I8expz3WkwQ004B')

        for news_item in news_items:
            title_tag = news_item.select_one(
                "a[data-heatmap-target='.tit'] span.sds-comps-text"
            )
            title = title_tag.get_text(strip=True) if title_tag else None

            body_tag = news_item.select_one(
                "a[data-heatmap-target='.body'] span.sds-comps-text"
            )
            body = body_tag.get_text(strip=True) if body_tag else None

            mark_tags = news_item.select(
                "a[data-heatmap-target='.body'] span.sds-comps-text mark")
            marks = [m.get_text(strip=True) for m in mark_tags]

            link_tag = news_item.select_one("a[data-heatmap-target='.tit']")
            link = link_tag.get("href") if link_tag else None

            date_tag = news_item.select_one(
                "span.sds-comps-profile-info-subtext span.sds-comps-text")
            date = date_tag.get_text(strip=True) if date_tag else None

            press_tag = news_item.select_one(
                "div.sds-comps-profile-info-title span.sds-comps-text a span.sds-comps-text")
            press = press_tag.get_text(strip=True) if press_tag else None

            result.append({
                "제목": title,
                "본문": body,
                "강조된 언어": marks,
                "기사 링크": link,
                "작성일": date,
                "언론사": press
            })

        self.assertEqual(len(result), len(news_items))
        self.assertEqual(result[0]['제목'],
                         "송중기·송혜교 데이트 장소 간 엄지원 “나도 기도할래”")
        self.assertEqual(result[1]['제목'],
                         "K팝·K드라마 이어 K디저트·K도자기까지…스펙트럼 확장에 외신 '주목'")
