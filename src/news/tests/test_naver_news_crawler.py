from typing import List

from django.test import TestCase

from news.crawler import NaverNewsCrawler, NaverNewsItem


class TestNewsCrawling(TestCase):

    def test_naver_news_crawler(self):
        # given
        crawler = NaverNewsCrawler(
            query="태양의 후예",
            ds="2023.06.03",
            de="2023.09.30"
        )
        # when
        result: List[NaverNewsItem] = next(crawler)
        print(crawler.next_url)

        # then
        self.assertIsNotNone(crawler.next_url)
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0].title,
                         "송중기·송혜교 데이트 장소 간 엄지원 “나도 기도할래”"
                         )
        self.assertEqual(result[1].title,
                         "K팝·K드라마 이어 K디저트·K도자기까지…스펙트럼 확장에 외신 '주목'"
                         )
