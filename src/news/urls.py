from django.urls.conf import path

from news import views

urlpatterns = [
    path('', views.index, name='news-list'),
    path('setup/', views.setup_news, name='setup-news')

]
