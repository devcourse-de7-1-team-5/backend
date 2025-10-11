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

def extract_drama_meta_from_result_page(driver, timeout=3):
    # 드라마 총 회차 정보 추출
    wait = WebDriverWait(driver, timeout)

    # 1) span.text 안에 em.state(부작)가 함께 있는 블록을 우선 탐색
    selectors = [
        "//span[contains(@class,'text')][.//em[contains(@class,'state') and contains(.,'부작')]]",
        "//*[@class][contains(.,'부작') and .//em[contains(@class,'state')]]",
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
        return {"총부작": None, "원문": None}

    # 2) 총 부작 수
    try:
        em = container.find_element(By.XPATH, ".//em[contains(@class,'state') and contains(.,'부작')]")
        eps_text = em.text.strip()
    except Exception:
        eps_text = container.text.strip()

    eps_match = re.search(r"(\d+)\s*부작", eps_text)
    total_eps = int(eps_match.group(1)) if eps_match else None

    
    return { "총부작": total_eps }

def get_episode_rating_and_synopsis(driver, drama_title: str, episode_no: int, timeout: int = 3):
    # 네이버에서 `<드라마 제목> <n화>`를 검색해, '방송 에피소드' 모듈에서 시청률과 줄거리를 추출합니다.

    wait = WebDriverWait(driver, timeout)

    def _try_with_suffix(suffix: str):
        query = f"{drama_title} {episode_no}{suffix}"
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
    # options.add_argument("--start-maximized")   # 브라우저 창 최대화
    options.add_argument("--headless=new")    # 창을 안 띄우고 싶으면 주석 해제

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
    
    elif num_episodes > 30:
        print(f"{drama_title}: 30회차가 넘어가는 드라마입니다")
        driver.quit()
        return episodes_list
    
    print(f"{drama_title}: 총 {num_episodes} 부작")

    for i in range(1,num_episodes+1):
        res = get_episode_rating_and_synopsis(driver, drama_title, i)
        
        if all(value is None for value in res.values()):
            return []
        episodes_list.append(res)

    driver.quit()

    return episodes_list
