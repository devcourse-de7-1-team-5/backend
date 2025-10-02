from django.shortcuts import render

from .crawler import NaverNewsCrawler
from .models import News


# Create your views here.


def index(request):
    news_list = News.objects.all()
    return render(request, 'news/index.html', {'news_list': news_list})


def crawl(request):
    crawler = NaverNewsCrawler(
        query="태양의 후예",
        ds="2023.06.03",
        de="2023.06.04"
    )

    crawler_data = list(crawler)
    news_models = [News(
        title=x.title,
        content=x.content,
        date=x.date,
        press=x.press,
        link=x.link
    ) for news in crawler_data for x in news]

    # when
    News.objects.bulk_create(news_models, ignore_conflicts=True)
    news_list = News.objects.all()
    return render(request, 'news/index.html', {'news_list': news_list})
    return None
