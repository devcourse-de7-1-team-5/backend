from datetime import timedelta

from django.db.models.expressions import Exists, OuterRef
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from dramas.models import Drama, EpisodeInfo
from news.crawler import NaverNewsCrawler
from news.models import News


# Create your views here.


def index(request):
    news_list = News.objects.all()
    return render(request, 'news/index.html', {'news_list': news_list})


@api_view(['GET'])
def set_up_news(request):
    """
    현재 저장된 모든 드라마 목록 중 뉴스 정보가 크롤링되지 않은 드라마에 대해 뉴스 정보를 크롤링하여 저장
    :param request:
    :return:
    """
    dramas_with_episodes = Drama.objects.annotate(  # 에피소드가 있는 드라마 정보만 조회
        has_episode=Exists(
            EpisodeInfo.objects.filter(drama_id=OuterRef('pk'))
        )
    ).filter(has_episode=True)
    completed_dramas = []

    for drama in dramas_with_episodes:

        episodes = drama.episodes.order_by("episode_no")
        episode_with_periods: list[tuple[EpisodeInfo, str, str]] = []
        for i, ep in enumerate(episodes):
            start = ep.date
            if i < len(episodes) - 1:
                end = episodes[i + 1].date - timedelta(days=1)
            else:
                end = drama.end_date
            episode_with_periods.append((ep, start, end))

        crawler = NaverNewsCrawler(
            query=drama.title,
            ds=drama.start_date.strftime("%Y.%m.%d"),
            de=drama.end_date.strftime("%Y.%m.%d"),
            start='0'
        )
        news_models = []
        link_to_save = set()

        for page in crawler:
            for news in page:

                for ep, start, end in episode_with_periods:
                    if news.link in link_to_save:
                        break
                    if news.date is not None and start <= news.date <= end:
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
                        link_to_save.add(news.link)
                        break
        News.objects.bulk_create(news_models, ignore_conflicts=True)
        completed_dramas.append({
            "title": drama.title,
            "news_count": len(link_to_save)
        })

    return Response(
        {
            "completed_dramas": completed_dramas,
        }
    )
