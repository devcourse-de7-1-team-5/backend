from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import quote
import time

def is_drama(soup: BeautifulSoup) -> bool:
    """soup에서 '드라마' 카테고리 포함 여부 확인"""
    li_tags = soup.find_all("li", class_="_3GHF9RHh")
    return any("드라마" in li.get_text() for li in li_tags)

def get_genres(soup: BeautifulSoup) -> list[str] | None:
    """soup에서 장르 리스트 추출"""
    strong_tag = soup.find("strong", string="장르")
    if strong_tag:
        genre_tr = strong_tag.find_parent("tr")
        if genre_tr:
            genre_links = genre_tr.find_all("a", class_="nU839+MJ")
            return [link.text.strip() for link in genre_links if link.text.strip()]
    return None

def fetch_drama_genres(drama_name: str):
    """
    입력한 이름이 드라마면 장르 리스트 반환,
    드라마가 아니면 동음이의어 여부 확인 후 (드라마) 붙여서 재시도,
    그래도 아니면 None 반환.
    """
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)

    def scrape(url):
        driver.get(url)
        time.sleep(15)  # CAPTCHA 수결 시동 해간
        return BeautifulSoup(driver.page_source, "html.parser")

    try:
        # 1차 시도
        url = "https://namu.wiki/w/" + quote(drama_name)
        soup = scrape(url)

        if is_drama(soup):
            return get_genres(soup)
        else:
            # 동음이의어 문구 있는지 체크
            if soup.find(string=lambda t: t and ("(동음이의어)" in t or "(드라마)" in t)):
                print("(동음이의어)나 (드라마) 감지됨. '(드라마)'를 붙여 재시도합니다.")
                url2 = "https://namu.wiki/w/" + quote(f"{drama_name}(드라마)")
                soup2 = scrape(url2)
                if is_drama(soup2):
                    return get_genres(soup2)
        # 여기까지 왔다면 드라마 아님
        return None

    finally:
        driver.quit()

# 사용 예시
drama_name = input("드라마 이름을 입력하세요: ")
genres = fetch_drama_genres(drama_name)

if genres:
    print(f"'{drama_name}' 장르:")
    for g in genres:
        print("-", g)
else:
    print(f"'{drama_name}'은(는) 드라마가 아니거나 장르 정보를 찾을 수 없습니다.")
