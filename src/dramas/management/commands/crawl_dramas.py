from django.core.management.base import BaseCommand
from dramas.models import Drama  # [핵심 수정] DB 저장을 위해 Drama 모델 임포트
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

# 크롤링할 URL 목록 
URLS = [
    "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=2023%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&oquery=%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&tqi=jL3W0lqo1LVssRIvaCZssssssbK-485093&ackey=01m4trmd",
    "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=2024%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&oquery=2023%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&tqi=jL3W2dqo15Vssa2Nb2osssssseN-237701&ackey=bafa7vot",
    "https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=2025%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&oquery=2024%EB%B0%A9%EC%98%81%EC%A2%85%EB%A3%8C%ED%95%9C%EA%B5%AD%EB%93%9C%EB%9D%BC%EB%A7%88&tqi=jL3IJdqo1LVsslRcBqVssssstxh-146316&ackey=9plgtro4"
]

class Command(BaseCommand):
    help = '여러 연도의 네이버 종영 드라마 목록을 자동으로 끝까지 크롤링합니다.'

    def handle(self, *args, **kwargs): 
        self.stdout.write(">> 크롬 드라이버를 초기화합니다...")
        
        # 1. 드라이버 설정 (Headless 모드 추가)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')           # 창을 띄우지 않고 실행
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options) # 옵션 적용

        # 2. URL 목록 순회
        for url in URLS:
            # 현재 연도 표시
            try:
                year = url.split('%EB%9D%BC%EB%A7%88')[0].split('query=')[-1].split('%EB%B0%A9')[0] 
            except IndexError:
                year = "Unknown"
            
            self.stdout.write(self.style.NOTICE(f">> 크롤링 시작: {year}년 종영 드라마 목록"))
            self.stdout.write(self.style.NOTICE(f"============================================="))

            driver.get(url)
            
            current_page = 1 
            
            # 3. 페이지 루프 시작 (다음 버튼이 사라질 때까지)
            while True:
                self.stdout.write(f"\n--- 현재 크롤링 중인 페이지: {current_page} ---")
                
                time.sleep(2) # 페이지 로딩 대기

                # 4. 현재 페이지의 모든 개별 드라마 항목(<li>) 가져오기
                drama_items = driver.find_elements(By.CSS_SELECTOR, "ul.list_info._list_item li.info_box")
                self.stdout.write(f"  > 발견된 드라마 항목 수: {len(drama_items)}개")
                
                # 5. 드라마 데이터 추출 및 DB 저장
                for item in drama_items:
                    drama_data = {}
                    try:
                        # 제목, 방송사(채널) 추출
                        drama_data['title'] = item.find_element(By.CSS_SELECTOR, "strong.title a._text").text.strip()
                        channel_element = item.find_element(By.CSS_SELECTOR, "div.main_info a.broadcaster")
                        drama_data['channel'] = channel_element.text.strip()
                        
                        # 날짜 추출
                        info_text = item.find_element(By.CSS_SELECTOR, "div.main_info span.info_txt").text.strip()
                        date_period_text = info_text.replace(drama_data['channel'], "", 1).strip()
                        
                        if '~' in date_period_text:
                            start_str, end_str = date_period_text.split('~')
                            start_date_str = start_str.strip().strip('.')
                            end_date_str = end_str.strip().strip('.')

                            drama_data['start_date'] = datetime.strptime(start_date_str, "%Y.%m.%d").date()
                            drama_data['end_date'] = datetime.strptime(end_date_str, "%Y.%m.%d").date()
                        else:
                            continue # 날짜 정보 없으면 건너뛰기

                        # --- [핵심 수정: DB 저장 로직] ---
                        drama, created = Drama.objects.update_or_create(
                            title=drama_data['title'],
                            defaults={
                                'channel': drama_data['channel'],
                                'start_date': drama_data['start_date'],
                                'end_date': drama_data['end_date'],
                                'description': None, # 네이버 리스트 뷰에서 줄거리는 추출하지 않음
                            }
                        )
                        
                        self.stdout.write("-" * 35)
                        self.stdout.write(f"제목: {drama_data['title']}")
                        self.stdout.write(f"채널: {drama_data['channel']}")
                        self.stdout.write(f"기간: {drama_data['start_date']} ~ {drama_data['end_date']}")
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"  > DB 저장 완료 (신규)"))
                        else:
                            self.stdout.write(f"  > DB 저장 완료 (업데이트)")
                        # ---------------------------------
                        
                    except Exception as e:
                        # 예외 발생 시에도 루프는 계속 진행
                        self.stdout.write(self.style.ERROR(f"  > WARNING: 크롤링 중 오류 발생 - {e}"))
                        continue 

                
                # 6. 다음 페이지 이동 로직
                try:
                    # '다음' 버튼을 찾아 클릭 시도
                    next_button = driver.find_element(By.CSS_SELECTOR, "a.pg_next._next.on")
                    next_button.click()
                    current_page += 1
                    
                except Exception:
                    # 버튼을 찾을 수 없으면 (마지막 페이지) 현재 URL 크롤링 종료
                    self.stdout.write("\n>> '다음' 버튼을 찾을 수 없습니다. 해당 연도 크롤링 종료.")
                    break 

        # 7. 모든 URL 크롤링 완료 후 드라이버 종료
        driver.quit()
        self.stdout.write(self.style.SUCCESS('\n\n>> 모든 연도 드라마 크롤링 작업 완료!'))
        