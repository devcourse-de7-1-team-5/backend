import asyncio
from datetime import timedelta, datetime

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef

from dramas.models import Drama, EpisodeInfo
from news.crawler import NaverNewsCrawler
from news.models import News


class Command(BaseCommand):
    help = "모든 드라마별 뉴스를 비동기로 크롤링하고 데이터베이스에 저장합니다."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(">> 네이버 뉴스 크롤링을 시작합니다."))
        asyncio.run(self.main())
        self.stdout.write(self.style.SUCCESS(">> 모든 드라마의 뉴스 크롤링 작업이 완료되었습니다."))

    async def main(self):
        dramas = await self.get_dramas_with_episodes_async()
        self.stdout.write(f"총 {len(dramas)}개의 드라마에 대해 뉴스 크롤링을 수행합니다.\n")
        completed, failed = await self.crawl_all_dramas(dramas)

        self.stdout.write("-" * 50)
        for news_count, drama in completed:
            self.stdout.write(self.style.SUCCESS(
                f"  ✅ {drama.title}: {news_count}개 뉴스 저장 완료"))
        for drama, error in failed:
            self.stdout.write(
                self.style.ERROR(f"  ❌ {drama.title} 실패: {error}"))
        self.stdout.write("-" * 50)
        self.stdout.write(
            f"총 {len(completed)}개 드라마 뉴스 크롤링 성공, {len(failed)}개 드라마 뉴스 크롤링 실패"
        )


    async def crawl_all_dramas(self, dramas):
        """모든 드라마 크롤링을 병렬 수행"""
        tasks = [self.crawl_single_drama(drama) for drama in dramas]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        completed, failed = [], []
        for res, drama in zip(results, dramas):
            if isinstance(res, Exception):
                failed.append((drama, str(res)))
            else:
                completed.append((res, drama))
        return completed, failed

    async def crawl_single_drama(self, drama):
        """한 드라마의 뉴스를 크롤링하고 DB에 저장 후 뉴스 개수 반환"""
        self.stdout.write(self.style.NOTICE(f"▶ {drama.title} 크롤링 시작"))

        episode_periods = await self.get_episode_periods_async(drama)

        crawler = NaverNewsCrawler(
            query=drama.title,
            ds=drama.start_date.strftime("%Y.%m.%d"),
            de=(drama.end_date or datetime.now().date()).strftime("%Y.%m.%d"),
            start='0'
        )

        news_models = []
        saved_links = set()

        async for page in crawler:
            for news in page:
                for ep, start, end in episode_periods:
                    if news.link in saved_links:
                        continue
                    if news.date and start <= news.date <= end:
                        news_models.append(
                            News(
                                title=news.title,
                                content=news.content,
                                date=news.date,
                                press=news.press,
                                link=news.link,
                                drama_ep=ep,
                            )
                        )
                        saved_links.add(news.link)
                        break

        if news_models:
            await self.bulk_create_news_async(news_models)

        count = len(news_models)
        self.stdout.write(f"  - {drama.title} 뉴스 {count}개 저장 완료")
        return count

    @sync_to_async
    def get_dramas_with_episodes_async(self):
        """에피소드가 존재하는 드라마만 조회"""
        return list(Drama.objects.annotate(
            has_episode=Exists(
                EpisodeInfo.objects.filter(drama_id=OuterRef('pk')))
        ).filter(has_episode=True))

    @sync_to_async
    def get_episode_periods_async(self, drama):
        """드라마의 에피소드별 뉴스 수집 기간 계산"""
        episodes = list(drama.episodes.order_by("episode_no"))
        periods = []
        for i, ep in enumerate(episodes):
            start = ep.date
            end = episodes[i + 1].date - timedelta(days=1) if i < len(
                episodes) - 1 else drama.end_date
            periods.append((ep, start, end))
        return periods

    @sync_to_async
    def bulk_create_news_async(self, news_list):
        """뉴스 목록을 한 번에 DB에 저장"""
        News.objects.bulk_create(news_list, ignore_conflicts=True)
