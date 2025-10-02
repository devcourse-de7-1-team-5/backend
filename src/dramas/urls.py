from django.urls import path
from . import views
from dramas.views import DramaList, DramaDetail

urlpatterns = [
    path('dramas/', DramaList.as_view(), name='drama-list'),
    path('dramas/<int:pk>/', DramaDetail.as_view(), name='drama-detail'),
]
