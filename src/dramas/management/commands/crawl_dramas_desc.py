from django.core.management.base import BaseCommand
from dramas.models import Drama 
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time

class Command(BaseCommand):
    help = 'DB의 드라마 제목을 Selenium으로 검색하여 줄거리를 업데이트합니다.'

    def handle(self, *args, **kwargs):
        self.stdout.write(">> 크롬 드라이버를 초기화합니다...")
        
        # 1. 드라이버 설정 
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')     #창 띄우지 않고 실행   
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        self.stdout.write(self.style.NOTICE(">> 줄거리 업데이트를 시작합니다..."))
        
        # 2. DB에서 줄거리가 없는(혹은 모든) Drama 객체 가져오기
        dramas = Drama.objects.filter(description__isnull=True).order_by('id')  #줄거리가 None인 것만 가져오기
        total_count = dramas.count()
        self.stdout.write(f"총 {total_count}개의 줄거리 미등록 드라마를 처리합니다.")

        updated_count = 0
        
        # 3. 각 드라마에 대해 순회하며 줄거리 크롤링
        for i, drama in enumerate(dramas):
            self.stdout.write(f"\n[{i+1}/{total_count}] 제목: {drama.title} 처리 중...")
            
            # 네이버 검색 URL 구성
            search_query = f"{drama.title}"
            search_url = f"https://search.naver.com/search.naver?query={search_query}"
            
            try:
                driver.get(search_url)
                time.sleep(2) # 페이지 로딩 대기

                # 4. 줄거리 요소 찾기 
                description_element = driver.find_element(By.CSS_SELECTOR, "div.text_expand span.desc._text" )
                
                description = description_element.text.strip()
                
                if description and len(description) > 10:
                    # 5. DB 업데이트
                    Drama.objects.filter(id=drama.id).update(description=description)
                    self.stdout.write(self.style.SUCCESS("  > 줄거리 업데이트 완료."))
                    updated_count += 1
                else:
                    self.stdout.write("  > 줄거리를 찾았으나 내용이 너무 짧거나 부적절합니다. 건너뜁니다.")
                    
            except NoSuchElementException:
                # 줄거리 요소(CSS)를 찾지 못했을 때 발생하는 예외
                self.stdout.write(self.style.ERROR("  > 줄거리 요소를 찾지 못했습니다."))
            except Exception as e:
                # 기타 오류 처리
                self.stdout.write(self.style.ERROR(f"  > 예상치 못한 오류 발생: {e.__class__.__name__}"))
            
            time.sleep(1) 

        driver.quit()
        self.stdout.write(self.style.SUCCESS(f"\n\n>> Selenium 줄거리 업데이트 작업 완료! 총 {updated_count}개 업데이트됨."))