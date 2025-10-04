from django.test import TestCase
from django.core.management import call_command
from dramas.models import Drama
from unittest.mock import patch, MagicMock
from datetime import date


class CrawlDramasCommandTest(TestCase):
    @patch("selenium.webdriver.Chrome")
    def test_crawl_dramas_command(self, mock_chrome):
    # 1. 가짜 웹드라이버 객체 생성(실제 크롬 실행 안되고 mock_driver 실행됨)
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver

        # 2. 드라마 항목(Mock HTML 요소) 구성
        mock_item = MagicMock()

        # 제목,방송사,방영일,종영일 항목(드라마 항목 담고 있는 컨테이너에서 해당 정보 html 위치)
        mock_item.find_element.side_effect = lambda by, selector: {
            "strong.title a._text": MagicMock(text="폭군의 셰프"),
            "div.main_info a.broadcaster": MagicMock(text="tvN"),
            "div.main_info span.info_txt": MagicMock(text="2025.08.23 ~ 2025.08.28 tvN"),
        }[selector]

        # 실제로는 여러 드라마 정보 담고 있는 <li>니오지만 여기서는 1개만 
        mock_driver.find_elements.return_value = [mock_item]

        # '다음' 버튼 없다고 처리 (페이지 로직)
        mock_driver.find_element.side_effect = Exception("No next button")

        # 3. 커맨드 실행
        call_command("crawl_dramas")

        # 4. DB 검증
        drama = Drama.objects.first()
        assert drama is not None
        assert drama.title == "폭군의 셰프"
        assert drama.channel == "tvN"
        assert drama.start_date == date(2025, 8, 23)
        assert drama.end_date == date(2025, 8, 28)