import asyncio
import time

from django.db.models.expressions import OuterRef, Exists
from django.test import TransactionTestCase
from django.urls.base import reverse

from dramas.models import Drama, EpisodeInfo
from news.models import News


class TestAsync(TransactionTestCase):
    def setUp(self):
        self.drama1 = Drama(
            title="태양의 후예",
            start_date="2016-02-24",
            end_date="2016-04-14",
        )
        self.drama1.save()
        self.drama_ep1 = EpisodeInfo(
            drama=self.drama1,
            episode_no=1,
            date='2016-02-24',
            rating="28.3",
            query="태양의 후예 1화",
            source_url="example.com"
        )
        self.drama_ep2 = EpisodeInfo(
            drama=self.drama1,
            episode_no=2,
            date='2016-02-25',
            rating="28.3",
            query="태양의 후예 2화",
            source_url="example.com"
        )
        self.drama_ep3 = EpisodeInfo(
            drama=self.drama1,
            episode_no=3,
            date='2016-03-02',
            rating="28.3",
            query="태양의 후예 3화",
            source_url="example.com"
        )
        self.drama_ep3.save()
        self.drama_ep2.save()
        self.drama_ep1.save()

        self.drama2 = Drama(
            title="이태원 클라쓰",
            start_date="2020-01-31",
            end_date="2020-03-21",
        )
        self.drama2.save()
        self.drama2_ep1 = EpisodeInfo(
            drama=self.drama2,
            episode_no=1,
            date='2020-01-31',
            rating="28.3",
            query="이태원 클라쓰 1화",
            source_url="example.com"
        )
        self.drama2_ep2 = EpisodeInfo(
            drama=self.drama2,
            episode_no=2,
            date='2020-02-01',
            rating="28.3",
            query="이태원 클라쓰 2화",
            source_url="example.com"
        )
        self.drama2_ep2.save()
        self.drama2_ep1.save()

        self.assertEqual(Drama.objects.count(), 2)

    def test_async_crawl_api(self):
        # given
        url = reverse("setup-news")
        dramas_with_episodes = Drama.objects.annotate(
            has_episode=Exists(
                EpisodeInfo.objects.filter(drama_id=OuterRef('pk'))
            )
        ).filter(has_episode=True)

        # when
        response = self.client.get(url)
        saved_dramas = dict((drama['title'], drama['news_count']) for drama in
                            response.data['completed_dramas'])
        print(response.data)

        # then
        for drama in dramas_with_episodes:
            ep_ids = drama.episodes.values_list('id', flat=True)
            self.assertIn(drama.title, saved_dramas.keys())

            news_count = News.objects.filter(drama_ep_id__in=ep_ids).count()
            self.assertEqual(news_count, saved_dramas[drama.title])

    def test_async_basic(self):
        titles = ["태양의 후예", "이태원 클라쓰", "스카이 캐슬"]
        expected_titles = ["드라마 " + t for t in titles]

        start_time = time.perf_counter()
        results = asyncio.run(self._run_crawling(titles))
        elapsed = time.perf_counter() - start_time

        self.assertCountEqual(results, expected_titles)
        self.assertLess(elapsed, 3.0)

        print(f"\n 총 실행 시간: {elapsed:.2f}s")
        print(f"최종 결과: {results}")

    async def _run_crawling(self, titles):
        tasks = [self._crawler_mock_function(t) for t in titles]
        completed = []

        for coro in asyncio.as_completed(tasks):
            result = await coro
            print(f"크롤링 완료: {result}")
            completed.append(result)

        print("모든 크롤링 완료")
        return completed

    async def _crawler_mock_function(self, title: str) -> str:
        print(f"start: {title}")
        await asyncio.sleep(1)
        print(f"done: {title}")
        return "드라마 " + title
