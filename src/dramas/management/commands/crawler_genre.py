# dramas/management/commands/crawler_genre.py

from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import quote
from dramas.models import Drama, Genre
import time


# -------------------------------
# 크롤링 유틸 함수
# -------------------------------
def is_drama(soup: BeautifulSoup) -> bool:
    """soup에서 '드라마' 카테고리 포함 여부 확인"""
    li_tags = soup.find_all("li")
    return any("드라마" in li.get_text() for li in li_tags)


def get_genres(soup: BeautifulSoup) -> list[str] | None:
    """soup에서 장르 리스트 추출"""
    strong_tag = soup.find("strong", string="장르")
    if strong_tag:
        genre_tr = strong_tag.find_parent("tr")
        if genre_tr:
            genre_links = genre_tr.find_all("a")
            genres = [link.text.strip() for link in genre_links if link.text.strip()]
            return genres if genres else None
    return None


def get_drama_genre(drama_name: str) -> list[str] | None:
    """
    드라마 이름으로 나무위키에서 장르 리스트 반환
    예: ["로맨스", "코미디"]
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)

    def scrape(url):
        driver.get(url)
        time.sleep(3)  # CAPTCHA 대응용 대기
        return BeautifulSoup(driver.page_source, "html.parser")

    try:
        url = "https://namu.wiki/w/" + quote(drama_name)
        soup = scrape(url)

        if is_drama(soup):
            return get_genres(soup)

        # 동음이의어 처리
        if soup.find(string=lambda t: t and ("동음이의어" in t or "(드라마)" in t)):
            retry_url = "https://namu.wiki/w/" + quote(f"{drama_name}(드라마)")
            soup_retry = scrape(retry_url)
            if is_drama(soup_retry):
                return get_genres(soup_retry)

        return None

    finally:
        driver.quit()


def save_drama_genres(drama_title: str):
    """DB에 장르 저장"""
    try:
        drama = Drama.objects.get(title=drama_title)
    except Drama.DoesNotExist:
        print(f"드라마 '{drama_title}' 없음")
        return

    genres = get_drama_genre(drama_title)
    if not genres:
        print(f"'{drama_title}' 장르 정보 없음")
        return

    # 기존 장르 삭제 후 추가
    drama.genres.all().delete()

    for g in genres:
        Genre.objects.create(drama=drama, name=g)

    print(f"'{drama_title}' 장르 저장 완료: {', '.join(genres)}")


# -------------------------------
# Django Management Command
# -------------------------------
class Command(BaseCommand):
    help = "DB에 있는 모든 드라마 제목 기준으로 장르 크롤링 후 저장"

    def handle(self, *args, **options):
        dramas = Drama.objects.all()
        if not dramas:
            self.stdout.write(self.style.WARNING("등록된 드라마가 없습니다."))
            return

        for drama in dramas:
            self.stdout.write(f"'{drama.title}' 장르 크롤링 중...")
            save_drama_genres(drama.title)
