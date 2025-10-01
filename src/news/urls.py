from django.urls.conf import path

from news import views

urlpatterns = [
    path('', views.index, name='news-list'),
    path('crawl/', views.crawl, name='news-crawl')

]
