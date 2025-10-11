from django.urls import path

from . import views

urlpatterns = [
    path('', views.drama_list_view, name='drama-list'),
    path('<int:pk>/', views.drama_detail_view, name='drama-detail'),
    path('check_data_status/', views.check_data_status,
         name='check_data_status'),
    path('setup_data/', views.setup_data, name='setup_data'),
    path('api/dashboard_metrics/', views.dashboard_metrics,
         name='dashboard_metrics'),
    path('api/', views.DramaList.as_view(), name='drama-list-api'),
    path('api/<int:pk>/', views.DramaDetail.as_view(), name='drama-detail-api'),
]
