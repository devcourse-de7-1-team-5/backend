from django.test import TestCase
from unittest.mock import patch, MagicMock
from dramas.management.commands.crawler_genre import get_drama_genre

class WikiCrawlerTest(TestCase):
    @patch("dramas.management.commands.crawler_genre.BeautifulSoup")
    @patch("selenium.webdriver.Chrome")
    def test_get_drama_genre(self, mock_chrome, mock_bs4):
        """
        Selenium과 BeautifulSoup를 mock 처리하여
        get_drama_genre 함수가 정상적으로 리스트 또는 None 반환하는지 테스트
        """

        # 1. 가짜 웹드라이버 생성
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # 2. 가짜 BeautifulSoup 객체 생성
        mock_soup = MagicMock()
        mock_soup.find_all.return_value = [MagicMock(text="드라마")]  # is_drama용
        mock_soup.find.return_value = None  # get_genres용

        mock_bs4.return_value = mock_soup

        # 3. 페이지 소스 mock
        mock_driver.page_source = "<html></html>"

        # 4. 함수 실행
        result = get_drama_genre("도깨비")

        # 5. 결과 검증: None 또는 list
        self.assertTrue(result is None or isinstance(result, list))
