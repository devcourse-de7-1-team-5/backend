from typing import List

from django.test import TestCase

from news.crawler import NaverNewsCrawler, NaverNewsItem
from news.models import News


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

        # then
        self.assertIsNotNone(crawler.next_url)
        self.assertEqual(len(result), 10)
        self.assertEqual(result[0].title,
                         "송중기·송혜교 데이트 장소 간 엄지원 “나도 기도할래”"
                         )
        self.assertEqual(result[1].title,
                         "K팝·K드라마 이어 K디저트·K도자기까지…스펙트럼 확장에 외신 '주목'"
                         )

    def test_news_duplicates_not_saved(self):
        """
        bulk_create 시 중복 링크는 무시되어
        DB에 동일한 뉴스가 두 번 저장되지 않아야 한다.
        """
        # given
        crawler = NaverNewsCrawler(
            query="태양의 후예",
            ds="2023.06.03",
            de="2023.06.04"
        )

        crawler_data = list(crawler)
        result_count = sum([len(news) for news in crawler_data])
        news_models = [News(
            title=x.title,
            content=x.content,
            date=x.date,
            press=x.press,
            link=x.link
        ) for news in crawler_data for x in news]

        # when
        News.objects.bulk_create(news_models, ignore_conflicts=True)
        News.objects.bulk_create(news_models, ignore_conflicts=True)

        # then
        self.assertEqual(News.objects.count(), result_count)
