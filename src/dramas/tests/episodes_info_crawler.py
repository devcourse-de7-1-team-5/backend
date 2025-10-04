# import os
# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # 프로젝트에 맞게
# django.setup()

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from urllib.parse import quote_plus

from selenium.common.exceptions import TimeoutException, NoSuchElementException

# from todo.models import Drama

def parse_dates_and_eps(text: str):
    """
    '2024.03.09. ~ 2024.04.28.' 같은 문자열에서
    시작일, 종료일을 추출 (문자열 그대로 반환)
    """
    # ~, –, -, ~ 사이 공백 등 다양한 구분자 수용
    # 날짜 표기: 2024.03.09. / 2024.3.9 / 2024-03-09 등 변형 수용
    date_pattern = r"(\d{4}[.\-\/]\s*\d{1,2}[.\-\/]\s*\d{1,2}\.?)"
    # 시작일 ~ 종료일 캡처
    m = re.search(date_pattern + r"\s*[~\-–]\s*" + date_pattern, text)
    if m:
        start_raw = re.sub(r"\s+", "", m.group(1))  # 공백 제거
        end_raw   = re.sub(r"\s+", "", m.group(2))
        # 끝의 마침표는 보기 좋게 제거
        start_raw = start_raw.rstrip(".")
        end_raw   = end_raw.rstrip(".")
        return start_raw, end_raw
    return None, None

def extract_drama_meta_from_result_page(driver, timeout=10):
    """
    네이버 검색 결과 페이지에서
    - 방영 시작/종료일
    - 총 부작 수
    를 추출하여 dict로 반환
    """
    wait = WebDriverWait(driver, timeout)

    # 1) span.text 안에 em.state(부작)가 함께 있는 블록을 우선 탐색
    selectors = [
        "//span[contains(@class,'text')][.//em[contains(@class,'state') and contains(.,'부작')]]",
        # 백업: 정보패널 내 유사 텍스트 블록
        "//*[@class][contains(.,'부작') and .//em[contains(@class,'state')]]",
        # 최후: '부작'을 담은 em.state를 직접 찾고 상위 텍스트에서 날짜 뽑기
        "//em[contains(@class,'state') and contains(.,'부작')]",
    ]

    container = None
    for xp in selectors:
        try:
            container = wait.until(EC.presence_of_element_located((By.XPATH, xp)))
            break
        except Exception:
            continue

    if container is None:
        return {"방영시작일": None, "방영종료일": None, "총부작": None, "원문": None}

    # 2) 총 부작 수
    # em.state 안의 "16부작"에서 숫자만 추출
    try:
        em = container.find_element(By.XPATH, ".//em[contains(@class,'state') and contains(.,'부작')]")
        eps_text = em.text.strip()
    except Exception:
        # 백업: 현재 요소 자체가 em일 수도 있으므로
        eps_text = container.text.strip()

    eps_match = re.search(r"(\d+)\s*부작", eps_text)
    total_eps = int(eps_match.group(1)) if eps_match else None

    # 3) 방영기간(시작/종료일)
    # container의 전체 텍스트에서 날짜 구간 추출 (부작 텍스트는 제거)
    whole_text = container.get_attribute("textContent") or container.text
    whole_text = whole_text.replace(eps_text, " ")
    whole_text = re.sub(r"\s+", " ", whole_text).strip()

    start_date, end_date = parse_dates_and_eps(whole_text)

    return {
        "방영시작일": start_date,     # 예: '2024.03.09'
        "방영종료일": end_date,       # 예: '2024.04.28'
        "총부작": total_eps,          # 예: 16 (int)
        "원문": whole_text            # 디버깅용 원문 텍스트
    }

# === 사용 예시 ===
# (전 단계에서 이미 네이버 검색 결과 페이지로 이동해 있다고 가정)
# meta = extract_drama_meta_from_result_page(driver)
# print(meta)

def get_episode_rating_and_synopsis(driver, drama_title: str, episode_no: int, timeout: int = 10):

    """
    네이버에서 `<드라마 제목> <n화>`를 검색해,
    '방송 에피소드' 모듈에서 시청률과 줄거리를 추출합니다.
    """
    wait = WebDriverWait(driver, timeout)

    def _try_with_suffix(suffix: str):
        query = f"{drama_title} {episode_no}{suffix}"
        # url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&query={quote_plus(query)}"
        url = f"https://search.naver.com/search.naver?query={quote_plus(query)}"
        driver.get(url)

        try:
            # '방송 에피소드' 모듈 컨테이너 (sc_new cs_common_module ... _kgs_broadcast_episode ...)
            module = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class,'_kgs_broadcast_episode')]"
            ))
        )
        except TimeoutException:
            print("방송 에피소드 요소를 찾지 못했습니다 (Timeout).")
            return {"회차": None, "방영일자": None, "시청률": None, "줄거리": None, "query": None, "source_url": None}
        except NoSuchElementException:
            print("방송 에피소드 요소 자체가 존재하지 않습니다.")
            return {"회차": None, "방영일자": None, "시청률": None, "줄거리": None, "query": None, "source_url": None}


        # --- 시청률 ---
        # dl.info 안에서 dt='시청률'인 그룹의 dd/em.value를 타겟
        try:
            rating_el = module.find_element(
            By.XPATH,
            ".//dl[contains(@class,'info')]//div[contains(@class,'info_group')][.//dd[em[contains(@class,'value')]]]//dd/em[contains(@class,'value')]"
            )
            rating = rating_el.text.strip()[:-1]
        except NoSuchElementException:
            rating = None
        
        # # --- 줄거리 ---
        # # 줄거리 텍스트 영역 (span.desc._text). '펼쳐보기' 버튼이 있으면 먼저 클릭
        # try:
        #     more_btn = module.find_element(By.XPATH, ".//button[contains(@class,'story_more')]")
        #     if more_btn.is_displayed():
        #         driver.execute_script("arguments[0].click();", more_btn)
        #         time.sleep(0.2)
        # except Exception:
        #     pass

        try:
            syn_el = module.find_element(
            By.XPATH,
            ".//div[contains(@class,'text_expand')]//span[contains(@class,'_text')]"
            )
            synopsis = syn_el.text.strip()
        except NoSuchElementException:
            synopsis = None
        

        # --- 방영일 ---
        try:
            date_group = module.find_element(
            By.XPATH,
            ".//dl[contains(@class,'info')]//div[contains(@class,'info_group')][.//dt[contains(.,'방송일')]]"
            )
            dd_elem = date_group.find_element(By.TAG_NAME, "dd")
            raw_text = dd_elem.text.strip()
            date = raw_text.split()[0].rstrip(".").replace(".", "-")
        except NoSuchElementException:
            date = None
        
        
        return {
            "episode_no": episode_no,
            "date": date,
            "rating": rating,
            "synopsis": synopsis,
            "query": query,
            "source_url": url
        }

    try:
        return _try_with_suffix("회")
    except Exception as e:
        print(e)
        return {"episode_no": None,
            "date": None,
            "rating": None,
            "synopsis": None,
            "query": None,
            "source_url": None
        }

def get_all_episode_info(drama_title: str):

    episodes_list = []

    # 크롬 옵션 설정
    options = Options()
    options.add_argument("--start-maximized")   # 브라우저 창 최대화
    # options.add_argument("--headless=new")    # 창을 안 띄우고 싶으면 주석 해제

    # Selenium Manager 사용 → Service 지정 필요 없음
    driver = webdriver.Chrome(options=options)

    # 네이버 접속
    driver.get("https://www.naver.com")
    
    # 검색창 찾기
    search_box = driver.find_element(By.ID, "query")  # 네이버 메인 검색창 id="query"
    
    search_box.send_keys(drama_title)

    # Enter 키 입력
    search_box.send_keys(Keys.RETURN)

    # 검색 결과 페이지 로딩 대기
    time.sleep(2)

    meta = extract_drama_meta_from_result_page(driver)

    num_episodes = meta["총부작"]

    if num_episodes == None:
        print("총 회차 수 정보가 없습니다")
        driver.quit()
        return episodes_list

    for i in range(1,num_episodes+1):
        res = get_episode_rating_and_synopsis(driver, drama_title, i)
        # print(res)
        # print(drama_title + " ",num_episodes)
        episodes_list.append(res)

    driver.quit()

    return episodes_list
