from django.urls.conf import path

from news import views


urlpatterns = [
    path('', views.index, name='news-list'),
    path('set-up/', views.set_up_news, name='set-up-news')

]
