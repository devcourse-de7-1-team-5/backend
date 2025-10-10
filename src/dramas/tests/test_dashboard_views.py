from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, ANY

from dramas.models import Drama, EpisodeInfo
from news.models import News

class DashboardViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # 테스트용 데이터 생성
        self.drama1 = Drama.objects.create(title="시청률 1위 드라마", start_date="2025-01-01")
        self.drama2 = Drama.objects.create(title="언급 1위 드라마", start_date="2025-01-02")
        self.drama3 = Drama.objects.create(title="그냥 드라마", start_date="2025-01-03")

        self.ep1_drama1 = EpisodeInfo.objects.create(drama=self.drama1, episode_no=1, date="2025-01-01", rating=9.5)
        self.ep2_drama1 = EpisodeInfo.objects.create(drama=self.drama1, episode_no=2, date="2025-01-02", rating=9.7) # AVG: 9.6

        self.ep1_drama2 = EpisodeInfo.objects.create(drama=self.drama2, episode_no=1, date="2025-01-02", rating=8.0)
        self.ep2_drama2 = EpisodeInfo.objects.create(drama=self.drama2, episode_no=2, date="2025-01-03", rating=8.2) # AVG: 8.1

        self.ep1_drama3 = EpisodeInfo.objects.create(drama=self.drama3, episode_no=1, date="2025-01-03", rating=9.0) # AVG: 9.0

        # '언급 1위 드라마'(drama2)에 대한 뉴스 3개 생성
        News.objects.create(title="뉴스1", drama_ep=self.ep1_drama2)
        News.objects.create(title="뉴스2", drama_ep=self.ep1_drama2)
        News.objects.create(title="뉴스3", drama_ep=self.ep2_drama2)

        # '시청률 1위 드라마'(drama1)에 대한 뉴스 1개 생성
        News.objects.create(title="뉴스4", drama_ep=self.ep1_drama1)

    def test_check_data_status_with_data(self):
        """데이터가 있을 때 check_data_status 뷰 테스트"""
        response = self.client.get(reverse('check_data_status'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data_exists'])

    def test_check_data_status_no_data(self):
        """데이터가 없을 때 check_data_status 뷰 테스트"""
        Drama.objects.all().delete()
        response = self.client.get(reverse('check_data_status'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['data_exists'])

    @patch('dramas.views.call_command')
    def test_setup_data_view(self, mock_call_command):
        """setup_data 뷰가 call_command를 호출하는지 테스트"""
        response = self.client.get(reverse('setup_data'))
        self.assertEqual(response.status_code, 200)
        mock_call_command.assert_called_once_with('setup_data', stdout=ANY)
        self.assertEqual(response.json()['status'], 'success')

    def test_dashboard_metrics_view(self):
        """dashboard_metrics 뷰의 데이터 정확성 테스트"""
        response = self.client.get(reverse('dashboard_metrics'))
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # 1. 시청률 랭킹 테스트
        top_rated_dramas = data['top_rated_dramas']
        self.assertEqual(len(top_rated_dramas), 3)
        # 순서 확인: drama1 (9.6) > drama3 (9.0) > drama2 (8.1)
        self.assertEqual(top_rated_dramas[0]['title'], '시청률 1위 드라마')
        self.assertEqual(top_rated_dramas[0]['avg_rating'], 9.6)
        self.assertEqual(top_rated_dramas[1]['title'], '그냥 드라마')
        self.assertEqual(top_rated_dramas[2]['title'], '언급 1위 드라마')

        # 2. 가장 많이 언급된 드라마 테스트
        most_mentioned = data['most_mentioned_drama']
        self.assertIsNotNone(most_mentioned)
        self.assertEqual(most_mentioned['drama__title'], '언급 1위 드라마')
        self.assertEqual(most_mentioned['mention_count'], 3)

    def test_dashboard_metrics_no_news(self):
        """뉴스 데이터가 없을 때 dashboard_metrics 뷰 테스트"""
        News.objects.all().delete()
        response = self.client.get(reverse('dashboard_metrics'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data['most_mentioned_drama'])
