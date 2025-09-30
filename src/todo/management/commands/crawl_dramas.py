from django.core.management.base import BaseCommand
from todo.models import Drama, ExternalIDMapping 
from datetime import datetime, date 
from django.db import IntegrityError

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

from bs4 import BeautifulSoup
import time
import re
import urllib.parse 

# 2023년 1월 1일 이후 시작 드라마만 필터링하기 위한 기준 날짜
MIN_START_DATE = date(2023, 1, 1)
# 최대 대기 시간 설정 (초 단위) - 페이지 로드 시간 초과 방지를 위해 넉넉하게 30초로 설정
MAX_WAIT_TIME = 30 

class Command(BaseCommand):
    help = 'KBS 공식 페이지에서 드라마 메타데이터를 크롤링하여 저장합니다. (Selenium 기반)'
    
    # --- 1. handle 함수 (실행 진입점) ---
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('--- KBS 드라마 크롤링 시작 (Selenium 사용) ---'))
        
        # KBS 크롤링만 실행합니다. (MBC 크롤링은 제외되었습니다.)
        self._crawl_kbs_drama("KBS_DRAMA_OFFICIAL") 
        
        self.stdout.write(self.style.SUCCESS('--- 크롤링 완료 ---'))

    # --- 2. KBS 공식 페이지 크롤링 (무한 스크롤) ---
    def _crawl_kbs_drama(self, source_name): 

        self.stdout.write(f"\n>> {source_name} 데이터 수집 시작")
        
        # KBS 종영 드라마 목록 URL (무한 스크롤 기반 페이지)
        URL = "https://drama.kbs.co.kr/end.html?section_id=24650"
        
        new_count = 0 
        driver = None
        
        try:
            # 1. 기존 데이터 삭제 (2023년 이전 데이터 정리)
            old_dramas = Drama.objects.filter(start_date__lt=MIN_START_DATE)
            deleted_count = old_dramas.count()
            
            if deleted_count > 0:
                old_dramas.delete()
                self.stdout.write(self.style.WARNING(f"  > WARNING: {deleted_count}개의 2023년 이전 드라마 데이터가 데이터베이스에서 삭제되었습니다."))
            else:
                self.stdout.write("  > 2023년 이전 삭제할 드라마 데이터가 없습니다.")

            # 2. WebDriver 설정 및 초기화
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument("user-agent=Mozilla/50 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
            
            # 페이지 로드 타임아웃 설정
            driver.set_page_load_timeout(MAX_WAIT_TIME)
            
            self.stdout.write("  > WebDriver 초기화 성공. 페이지 로딩 시작...")
            
            # 3. 페이지 로드
            driver.get(URL)

            # 4. 동적 콘텐츠가 로드될 때까지 명시적으로 대기
            WebDriverWait(driver, MAX_WAIT_TIME).until(
                EC.presence_of_element_located((By.ID, "total_list"))
            )
            self.stdout.write("  > 동적 콘텐츠 로딩 완료.")

            # --- 무한 스크롤 로직 (이전 데이터 로드) ---
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            MAX_SCROLL_ATTEMPTS = 5 # 최대 5번 스크롤 시도

            while scroll_attempts < MAX_SCROLL_ATTEMPTS:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2) # 새로운 콘텐츠 로드를 기다림
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    self.stdout.write("  > 페이지 끝에 도달했거나 더 이상 로드할 콘텐츠가 없습니다.")
                    break
                
                last_height = new_height
                scroll_attempts += 1
                self.stdout.write(f"  > 스크롤 횟수: {scroll_attempts}. 추가 콘텐츠 로드됨.")
            
            self.stdout.write("  > 모든 콘텐츠 로드 시도 완료.")

            # 5. 로드된 페이지 소스 가져오기 (스크롤 후)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
        except TimeoutException as te:
            self.stdout.write(self.style.ERROR(f"[{source_name}] 크롤링 실패 (Timeout): {te}. **WebDriver의 페이지 로드 타임아웃을 30초로 설정했습니다. 네트워크 환경을 다시 확인하세요.**"))
            return 
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[{source_name}] 크롤링 실패 (Selenium 오류): {e}"))
            return 
        finally:
            if driver:
                driver.quit()

        # 6. BeautifulSoup으로 데이터 추출
        drama_list = soup.select('#total_list > div.comp-item')
        
        if not drama_list:
            self.stdout.write(self.style.ERROR(f"  > KBS: 로드된 페이지에서 드라마 아이템을 찾을 수 없습니다. (총 0개)"))
            return

        self.stdout.write(f"  > 총 {len(drama_list)}개의 드라마 아이템 발견. (스크롤 후)")

        for element in drama_list:
            crawled_title = "Unknown Title" 
            try:
                # 1. 제목 추출 (tit2 클래스)
                title_tag = element.select_one('.txt-box .tit2')
                if not title_tag: continue
                crawled_title = title_tag.text.strip()
                
                # 2. 날짜 추출 및 가공 (date 클래스)
                date_text_tag = element.select_one('.txt-box .date')
                if not date_text_tag:
                    self.stdout.write(self.style.WARNING(f"  > WARNING: [{crawled_title}] 날짜 정보가 없어 건너킵니다."))
                    continue

                date_text = date_text_tag.text.strip()
                
                # 정규식: YYYY.MM.DD 형식의 날짜 2개 추출
                date_matches = re.findall(r'(\d{4}\.\d{2}\.\d{2})', date_text)
                date_range = []

                for dt in date_matches:
                    formatted_date = dt.replace('.', '-')
                    date_range.append(formatted_date)

                
                if len(date_range) == 2:
                    crawled_start_date_str = date_range[0]
                    crawled_end_date_str = date_range[1]
                elif len(date_range) == 1:
                    # 시작일과 종료일이 같은 경우 (단막극 등)
                    crawled_start_date_str = date_range[0]
                    crawled_end_date_str = date_range[0]
                else:
                    self.stdout.write(self.style.WARNING(f"  > WARNING: [{crawled_title}] 날짜 형식 오류: 유효한 날짜를 찾을 수 없음 '{date_text}'. 건너킵니다."))
                    continue
                
                # 3. 상세 URL 및 External ID 추출
                link_tag = element.select_one('a[href]')
                if not link_tag: continue
                    
                crawled_detail_url = link_tag['href']
                # URL에서 슬러그(drama 이름)를 External ID로 사용합니다.
                match = re.search(r'/drama/([^/]+)', crawled_detail_url)
                if not match:
                    self.stdout.write(self.style.WARNING(f"  > WARNING: [{crawled_title}] 프로그램 슬러그를 찾을 수 없어 건너킵니다."))
                    continue
                kbs_id = match.group(1) 

                # 4. 날짜 객체로 변환 및 필터링 (2023년 1월 1일 이후 시작 드라마만)
                start_date = datetime.strptime(crawled_start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(crawled_end_date_str, '%Y-%m-%d').date()
                
                if start_date < MIN_START_DATE:
                    self.stdout.write(self.style.WARNING(f"  > WARNING: [{crawled_title}] 시작일 {start_date}가 기준({MIN_START_DATE}) 이전이므로 건너킵니다."))
                    continue
                
                # 현재 KBS 페이지에서는 이미지와 줄거리 추출 로직이 없으므로 None으로 둡니다.
                description = None

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  > ERROR: [{crawled_title}] 데이터 추출/형식 오류 - {e}"))
                continue

            # 5. DB 저장
            # KBS 페이지는 채널이 'KBS'로 고정
            drama, created = Drama.objects.get_or_create(
                title=crawled_title,
                defaults={
                    'channel': 'KBS',
                    'start_date': start_date, 
                    'end_date': end_date,
                    'description': description,
                }
            )

            # 6. ExternalIDMapping 테이블에 KBS ID 기록
            ExternalIDMapping.objects.get_or_create(
                drama=drama,
                source_name=source_name,
                external_id=kbs_id
            )
            
            if created:
                new_count += 1
            
            time.sleep(0.05)

        self.stdout.write(self.style.SUCCESS(f"  > {source_name}: 새로운 드라마 {new_count}개 생성 및 매핑 완료."))
