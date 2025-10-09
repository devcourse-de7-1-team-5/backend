from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = '드라마, 회차 정보, 뉴스 데이터를 순서대로 크롤링하여 초기 데이터를 설정합니다.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("===== 초기 데이터 설정을 시작합니다. ====="))

        try:
            # 1. 드라마 기본 정보 크롤링
            self.stdout.write(self.style.NOTICE("\n[1/3] 드라마 기본 정보 크롤링을 시작합니다..."))
            call_command('crawl_dramas')
            self.stdout.write(self.style.SUCCESS("[1/3] 드라마 기본 정보 크롤링 완료!"))

            # 2. 드라마 회차 정보 크롤링
            self.stdout.write(self.style.NOTICE("\n[2/3] 드라마 회차별 상세 정보 크롤링을 시작합니다..."))
            call_command('crawler_episodes')
            self.stdout.write(self.style.SUCCESS("[2/3] 드라마 회차별 상세 정보 크롤링 완료!"))

            # 3. 뉴스 정보 크롤링
            self.stdout.write(self.style.NOTICE("\n[3/3] 드라마 관련 뉴스 정보 크롤링을 시작합니다..."))
            call_command('crawl_news')
            self.stdout.write(self.style.SUCCESS("[3/3] 드라마 관련 뉴스 정보 크롤링 완료!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n초기 데이터 설정 중 오류가 발생했습니다: {e}"))
            self.stdout.write(self.style.WARNING("작업이 중단되었습니다. 로그를 확인해주세요."))
            return

        self.stdout.write(self.style.SUCCESS("\n===== 모든 초기 데이터 설정이 성공적으로 완료되었습니다. ====="))
