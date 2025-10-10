import asyncio
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db.models import Exists, OuterRef
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from dramas.models import Drama, EpisodeInfo
from news.crawler import NaverNewsCrawler
from news.models import News


def index(request):
    news_list = News.objects.all()
    return render(request, 'news/index.html', {'news_list': news_list})


@api_view(['GET'])
def set_up_news(request):
    """
    각 드라마별 뉴스 크롤링을 비동기로 수행하고,
    크롤링 완료 시마다 DB에 저장 후 완료/실패 드라마 반환
    """

    async def main():
        dramas = await get_dramas_with_episodes_async()
        completed, failed = await crawl_all_dramas(dramas)
        return completed, failed

    completed_results, failed_results = asyncio.run(main())

    completed_dramas_info = [
        {"title": drama.title, "news_count": news_count}
        for news_count, drama in completed_results
    ]
    failed_dramas_info = [
        {"title": drama.title, "error": error} for drama, error in
        failed_results
    ]

    return Response({
        "completed_dramas": completed_dramas_info,
        "failed_dramas": failed_dramas_info
    })


async def crawl_all_dramas(dramas):
    """
    모든 드라마 뉴스 크롤링을 병렬로 수행하고 결과 수집
    각 드라마별 (뉴스 개수, 드라마) 튜플 반환
    """
    tasks = [crawl_single_drama(drama) for drama in dramas]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    completed, failed = [], []
    for res, drama in zip(results, dramas):
        if isinstance(res, Exception):
            failed.append((drama, str(res)))
        else:
            # res는 이제 뉴스 개수(int)
            completed.append((res, drama))
    return completed, failed


async def crawl_single_drama(drama):
    """한 드라마의 뉴스를 크롤링하고 DB에 저장 후, 뉴스 개수를 반환"""
    print("start:", drama.title)
    episode_periods = await get_episode_periods_async(drama)

    crawler = NaverNewsCrawler(
        query=drama.title,
        ds=drama.start_date.strftime("%Y.%m.%d"),
        de=drama.end_date.strftime("%Y.%m.%d"),
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
        await bulk_create_news_async(news_models)

    print("completed:", drama.title, len(news_models))

    return len(news_models)


@sync_to_async
def get_dramas_with_episodes_async():
    """에피소드가 존재하는 드라마만 조회"""
    return list(Drama.objects.annotate(
        has_episode=Exists(EpisodeInfo.objects.filter(drama_id=OuterRef('pk')))
    ).filter(has_episode=True))


@sync_to_async
def get_episode_periods_async(drama):
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
def bulk_create_news_async(news_list):
    """뉴스 목록을 한 번에 DB에 저장"""
    News.objects.bulk_create(news_list, ignore_conflicts=True)
