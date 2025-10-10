from django.test.testcases import TestCase
from django.urls.base import reverse

from dramas.models import EpisodeInfo, Drama


class DramaEpisodesTest(TestCase):
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
            rating="1.3",
            query="태양의 후예 1화",
            source_url="example.com"
        )
        self.drama_ep2 = EpisodeInfo(
            drama=self.drama1,
            episode_no=2,
            date='2016-02-25',
            rating="2.3",
            query="태양의 후예 2화",
            source_url="example.com"
        )
        self.drama_ep3 = EpisodeInfo(
            drama=self.drama1,
            episode_no=3,
            date='2016-03-02',
            rating="3.3",
            query="태양의 후예 3화",
            source_url="example.com"
        )
        self.drama_ep3.save()
        self.drama_ep2.save()
        self.drama_ep1.save()

        self.assertEqual(Drama.objects.count(), 1)

    def test_episode_ordering(self):
        # given
        url = reverse("drama-detail", args=[self.drama1.id])

        # when
        # news_count 기준 정렬
        response_by_news = list(
            self.client.get(url, data={'order_by': '-news_count'}).context[
                'drama'].episodes.all())

        # rating 기준 정렬
        response_by_rating = list(
            self.client.get(url, data={'order_by': '-rating'}).context[
                'drama'].episodes.all())

        # episode_no 기준 정렬
        response_by_no = list(
            self.client.get(url, data={'order_by': 'episode_no'}).context[
                'drama'].episodes.all())

        # then
        for i in range(len(response_by_news) - 1):
            # 뉴스 많은 순 내림차순
            self.assertGreaterEqual(response_by_news[i].news_count,
                                    response_by_news[i + 1].news_count)
            # 시청률 내림차순
            self.assertGreaterEqual(float(response_by_rating[i].rating or 0),
                                    float(
                                        response_by_rating[i + 1].rating or 0))
            # 회차 오름차순
            self.assertLessEqual(response_by_no[i].episode_no,
                                 response_by_no[i + 1].episode_no)
