import requests
from django.core.management.base import BaseCommand
from django.db.models import Q

from dramas.models import Drama
from common.bs4_util import parse_html_to_soup, get_image_src

# 네이버 검색 결과를 가져오는 기본 URL (드라마 제목이 들어갈 부분은 {}로 표시)
NAVER_SEARCH_URL = "https://search.naver.com/search.naver?query={}"


class Command(BaseCommand):
    help = 'Drama에 썸네일 URL이 없는 경우 네이버 검색을 통해 이미지 URL을 업데이트합니다.'

    def handle(self, *args, **options):
        # 썸네일 URL이 null이거나 빈 문자열인 드라마만 가져옵니다.
        dramas_to_update = Drama.objects.filter(
            Q(img_url__isnull=True) | Q(img_url='')
        )
        
        self.stdout.write(self.style.NOTICE(f'총 {dramas_to_update.count()}개의 드라마 썸네일을 업데이트합니다.'))
        
        updated_count = 0
        
        for drama in dramas_to_update:
            search_query = f"{drama.title} 드라마" # 정확한 검색을 위해 "드라마"를 추가
            search_url = NAVER_SEARCH_URL.format(search_query)

            try:
                # 1. 네이버 검색 결과 페이지 가져오기
                response = requests.get(search_url, timeout=5)
                response.raise_for_status()
                
                # 2. HTML 파싱
                soup = parse_html_to_soup(response.text)
                
                # 3. 이미지 URL 추출
                # 네이버 검색 결과에서 드라마 정보 블록 (이미지가 포함된 곳)을 찾습니다.
                # (이전 사용자 입력의 'div.detail_info' 기반으로 가정)
                detail_info_tag = soup.select_one('div.detail_info') 
                image_url = get_image_src(detail_info_tag)

                if image_url:
                    # 4. 이미지 URL 업데이트
                    drama.img_url = image_url
                    drama.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ {drama.title}: 썸네일 URL 업데이트 성공'))
                else:
                    self.stdout.write(self.style.WARNING(f'❌ {drama.title}: 검색 결과에서 이미지 태그를 찾을 수 없습니다.'))

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f'🚫 {drama.title}: 네이버 검색 요청 실패 - {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'⚠️ {drama.title}: 알 수 없는 오류 - {e}'))


        self.stdout.write(self.style.SUCCESS(f'\n--- 완료: 총 {updated_count}개의 썸네일이 업데이트되었습니다. ---'))