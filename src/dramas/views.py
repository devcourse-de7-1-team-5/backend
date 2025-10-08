from rest_framework import generics
from django.db.models import Q 
from .models import *
from .serializers import DramaListSerializer, DramaDetailSerializer, EpisodeInfoSerializer
from rest_framework import generics
from django.shortcuts import render
from dramas.models import Drama

from django.http import Http404
import requests
from django.views import View
from datetime import date 

class DramaList(generics.ListCreateAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaListSerializer


class DramaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaDetailSerializer

def drama_list_view(request):
    dramas = Drama.objects.all().order_by('start_date') #방영일 기준으로 드라마 목록 가져오기 
    # 검색어
    search_query = request.GET.get('query') #제목
    selected_year = request.GET.get('year') #년도
    selected_genre = request.GET.get('genre') #장르 

    # 검색어 필터링(제목)
    if search_query:
        dramas = dramas.filter(title__icontains=search_query)

    # 년도 
    if selected_year and selected_year != 'all':
        try:
            year_int = int(selected_year) 
            dramas = dramas.filter(start_date__year=year_int)
        except ValueError:
            pass

    # 장르
    if selected_genre and selected_genre != 'all':
        dramas = dramas.filter(genre__icontains=selected_genre)

    # 5. 컨텍스트 구성
    current_year = date.today().year
    year_list = list(range(2023, current_year + 1))
    genre_list = ['로맨스', '액션', '코미디', '스릴러', '판타지']
    
    context = {
        'dramas': dramas,
        'year_list': year_list,
        'genre_list': genre_list,
        'selected_year': selected_year if selected_year else 'all',
        'selected_genre': selected_genre if selected_genre else 'all',
        'search_query': search_query if search_query else '', 
    }
    return render(request, 'dramas/drama_list.html', context)

class DramaDetailView(View):
    def get(self, request, pk):
        try:
            res = requests.get(f"http://127.0.0.1:8000/dramas/{pk}", timeout=5)
            if res.status_code == 404:
                raise Http404("드라마를 찾을 수 없습니다.")
            res.raise_for_status()  # 200이 아닌 다른 상태코드일 때 예외 발생
            data = res.json()
        except requests.exceptions.RequestException as e:
            # 네트워크 오류, 타임아웃, 500 등
            raise Http404("드라마 정보를 불러올 수 없습니다.") from e
        return render(request, "dramas/drama_detail.html", {"drama": data})