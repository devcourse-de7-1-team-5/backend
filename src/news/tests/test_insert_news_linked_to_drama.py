from django.db.models.expressions import Exists, OuterRef
from django.test import TransactionTestCase
from django.urls import reverse

from dramas.models import Drama, EpisodeInfo
from news.models import News


class TestInsertNewsLinkedToDrama(TransactionTestCase):
    def setUp(self):
        self.drama_has_episode = Drama(
            title="태양의 후예",
            start_date="2016-02-24",
            end_date="2016-04-14",
        )
        self.drama_has_episode.save()
        self.drama_has_not_episode = Drama(
            title="drama_has_not_episode",
            start_date="2016-02-24",
            end_date="2016-04-14",
        )
        self.drama_has_not_episode.save()

        self.drama_ep1 = EpisodeInfo(
            drama=self.drama_has_episode,
            episode_no=1,
            date='2016-02-24',
            rating="28.3",
            query="태양의 후예 1화",
            source_url="example.com"
        )
        self.drama_ep2 = EpisodeInfo(
            drama=self.drama_has_episode,
            episode_no=2,
            date='2016-02-25',
            rating="28.3",
            query="태양의 후예 2화",
            source_url="example.com"
        )
        self.drama_ep3 = EpisodeInfo(
            drama=self.drama_has_episode,
            episode_no=3,
            date='2016-03-02',
            rating="28.3",
            query="태양의 후예 3화",
            source_url="example.com"
        )
        self.drama_ep3.save()
        self.drama_ep2.save()
        self.drama_ep1.save()

    def test_select_only_dramas_with_episodes(self):
        """
        에피소드를 하나 이상 가지고 있는 드라마만 선택하는지 테스트
        """
        # when
        dramas_with_episodes = Drama.objects.annotate(
            has_episode=Exists(
                EpisodeInfo.objects.filter(drama_id=OuterRef('pk'))
            )
        ).filter(has_episode=True)

        self.assertEqual(dramas_with_episodes.count(), 1)

        for v in dramas_with_episodes:
            self.assertTrue(v.has_episode)
            self.assertIsNotNone(v.pk)

    def test_check_inserting_news_to_correct_drama(self):
        # given
        url = reverse("setup-news")
        dramas_with_episodes = Drama.objects.annotate(  # 에피소드가 있는 드라마 정보만 조회
            has_episode=Exists(
                EpisodeInfo.objects.filter(drama_id=OuterRef('pk'))
            )
        ).filter(has_episode=True)


        # when
        response = self.client.get(url)
        saved_dramas = dict((drama['title'], drama['news_count']) for drama in
                            response.data['completed_dramas'])

        # then
        self.assertIsNotNone(url)
        self.assertTrue(response.status_code, 200)
        for drama in dramas_with_episodes:
            ep_ids = drama.episodes.values_list('id', flat=True)
            self.assertIn(drama.title, saved_dramas.keys())

            news_count = News.objects.filter(drama_ep_id__in=ep_ids).count()
            self.assertEqual(news_count, saved_dramas[drama.title])
