from typing import List

from django.test import TestCase

from common.date_util import parse_date_to_search
from dramas.models import EpisodeInfo, Drama
from news.crawler import NaverNewsCrawler, NaverNewsItem
from news.models import News


class TestNewsCrawling(TestCase):

    def generate_drama_mock(self):
        self.drama = Drama(
            title="태양의 후예",
            start_date="2016-02-24",
            end_date="2016-04-14",
        )

        self.drama.save()
        self.assertIsNotNone(self.drama.id)

        self.drama_ep7 = EpisodeInfo(
            drama=self.drama,
            episode_no=1,
            date='2016-03-16',
            rating="28.3",
            query="태양의 후예 7화",
            source_url="example.com"
        )
        self.drama_ep7.save()
        self.assertIsNotNone(self.drama_ep7.id)

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
            de="2023.09.14"
        )
        self.generate_drama_mock()
        data = next(crawler)

        crawler_data = data + data

        # 다음 페이지 조회 시작 인덱스 -1
        expected_count = int(crawler.params['start'])- 1


        news_models = [News(
            title=news.title,
            content=news.content,
            date=news.date,
            press=news.press,
            link=news.link,
            drama_ep_id=self.drama_ep7.id,
        ) for news in crawler_data]

        # when
        News.objects.bulk_create(news_models, ignore_conflicts=True)
        News.objects.bulk_create(news_models, ignore_conflicts=True)

        # then
        self.assertEqual(News.objects.count(), expected_count)

    def test_news_crawler_all_method(self):
        # given
        self.generate_drama_mock()
        search_ds = parse_date_to_search(str(self.drama.start_date))
        search_de = parse_date_to_search(str(self.drama.end_date))

        # when
        crawler = NaverNewsCrawler(
            query=self.drama.title,
            ds=search_ds,
            de=search_de
        )
        next_result: List[NaverNewsItem] = next(crawler)

        # then
        self.assertNotEquals(int(crawler.params['start']), 0)
        self.assertEqual(len(next_result),
                         int(crawler.params['start']) - 1)
