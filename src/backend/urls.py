"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

# from dramas.views import drama_list_view, DramaDetailView, drama_detail_view
from dramas.views import drama_list_view, drama_detail_view
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('dramas/', include('dramas.urls')),
    path('news/', include('news.urls')),
    path('dramas/',drama_list_view, name='drama-list-page'),
    path('dramas/<int:pk>/', drama_detail_view, name='drama-detail')

]
