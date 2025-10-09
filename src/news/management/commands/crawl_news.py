
import asyncio
from django.core.management.base import BaseCommand
from dramas.models import Drama
from news.models import News
from news.crawler import NaverNewsCrawler
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = "드라마별로 네이버 뉴스를 크롤링하여 데이터베이스에 저장합니다."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(">> 네이버 뉴스 크롤링을 시작합니다."))

        dramas = Drama.objects.all()
        if not dramas.exists():
            self.stdout.write(self.style.WARNING(">> 크롤링할 드라마 정보가 없습니다. `crawl_dramas`를 먼저 실행해주세요."))
            return

        for drama in dramas:
            # 방영 시작일과 종료일 설정
            start_date = drama.start_date
            end_date = drama.end_date if drama.end_date else datetime.now().date()
            
            # 종료일이 시작일보다 과거일 경우, 시작일로부터 1년으로 임의 설정
            if end_date < start_date:
                end_date = start_date + timedelta(days=365)

            ds = start_date.strftime("%Y.%m.%d")
            de = end_date.strftime("%Y.%m.%d")
            query = f'"{drama.title}"' # 정확한 검색을 위해 큰따옴표 사용

            self.stdout.write("-" * 50)
            self.stdout.write(self.style.NOTICE(f">> '{drama.title}'의 뉴스를 검색합니다. (기간: {ds} ~ {de})"))

            try:
                news_items = asyncio.run(self.fetch_news(query, ds, de))
                
                if not news_items:
                    self.stdout.write(self.style.WARNING("  - 발견된 뉴스가 없습니다."))
                    continue

                for item in news_items:
                    # News 모델에 맞게 데이터 저장 또는 업데이트
                    news_obj, created = News.objects.update_or_create(
                        link=item.link,
                        defaults={
                            'drama': drama,
                            'title': item.title,
                            'content': item.content,
                            'press': item.press,
                            'date': item.date,
                        }
                    )
                    if created:
                        self.stdout.write(f"  - 새로운 뉴스 저장: {item.title[:30]}...")
                    else:
                        self.stdout.write(f"  - 기존 뉴스 업데이트: {item.title[:30]}...")

                self.stdout.write(self.style.SUCCESS(f"  총 {len(news_items)}개의 뉴스 처리 완료."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ** 크롤링 중 오류 발생: {e}"))

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(">> 모든 드라마의 뉴스 크롤링 작업이 완료되었습니다."))

    async def fetch_news(self, query, ds, de):
        """비동기 크롤러를 실행하고 결과를 반환합니다."""
        crawler = NaverNewsCrawler(query=query, ds=ds, de=de)
        return await crawler.all()
