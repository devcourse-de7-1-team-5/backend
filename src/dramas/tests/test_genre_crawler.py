from django.test import TestCase
from dramas.management.commands.crawler_genre import get_drama_genre

class WikiCrawlerIntegrationTest(TestCase):
    def test_get_drama_genre_real(self):
        """
        실제 웹에서 크롤링을 수행하여 장르 리스트를 반환받는 테스트
        """
        drama_title = "폭군의 셰프"  # 실제 존재하는 드라마
        genres = get_drama_genre(drama_title)

        # 반환값 검증
        self.assertIsInstance(genres, list)
        self.assertGreater(len(genres), 0)  # 장르가 하나 이상 존재해야 함
        self.assertIsInstance(genres if genres is not None else [], list)
        print(f"{drama_title} 장르: {genres}")
