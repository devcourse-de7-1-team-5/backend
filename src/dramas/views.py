from rest_framework import generics
from django.db.models import Max, Value, FloatField, Count, ExpressionWrapper, F
from django.db.models.functions import ExtractYear, Coalesce
from django.db.models import Prefetch
from django.shortcuts import render
from datetime import date
import json

from dramas.serializers import DramaListSerializer, DramaDetailSerializer
from .models import Drama, EpisodeInfo

# --- REST API ---
class DramaList(generics.ListCreateAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaListSerializer

class DramaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaDetailSerializer

def drama_list_view(request):
    current_year = date.today().year

    # 기본 쿼리
    dramas = Drama.objects.prefetch_related('genres', 'episodes').annotate(
        max_rating=Coalesce(Max('episodes__rating'), Value(0.0), output_field=FloatField()),
        news_count=Coalesce(Count('episodes__query', distinct=True), Value(0))
    )

    # 필터링 파라미터
    search_query = request.GET.get('query', '')
    selected_year = request.GET.get('year', 'all')
    selected_genre = request.GET.get('genre', 'all')

    filtered_dramas = dramas

    # --- 검색 / 필터링 로직 ---
    if search_query:
        filtered_dramas = filtered_dramas.filter(title__icontains=search_query)
    if selected_year != 'all':
        filtered_dramas = filtered_dramas.filter(start_date__year=int(selected_year))
    if selected_genre != 'all':
        filtered_dramas = filtered_dramas.filter(genres__name=selected_genre).distinct()

    # 종합 점수 계산 (시청률 70%, 뉴스 30%)
    filtered_dramas = filtered_dramas.annotate(
        ranking_score=ExpressionWrapper(
            F('max_rating') * 0.7 + F('news_count') * 0.3,
            output_field=FloatField()
        )
    )

    # Top 10 추출
    top_10_dramas = filtered_dramas.order_by('-ranking_score')[:10]

    # --- 빈 경우 전체 Top 10 보여주기 ---
    if not top_10_dramas.exists():
        top_10_dramas = dramas.annotate(
            ranking_score=ExpressionWrapper(
                F('max_rating') * 0.7 + F('news_count') * 0.3,
                output_field=FloatField()
            )
        ).order_by('-ranking_score')[:10]

    # 차트용 데이터 구성
    chart_data_dict = [
        {
            'title': d.title,
            'max_rating': float(d.max_rating or 0),
            'news_count': int(d.news_count or 0),
            'score': float(d.ranking_score or 0),
        }
        for d in top_10_dramas
    ]

    # JSON 문자열로 직렬화 (템플릿에서 사용)
    chart_data_json = json.dumps(chart_data_dict, ensure_ascii=False)

    # 드라마 목록 (최신순)
    display_dramas = filtered_dramas.annotate(
        year=ExtractYear('start_date')
    ).order_by('-start_date')

    # 필터 리스트 (고정 장르)
    genre_list = ["로맨틱 코미디", "휴먼", "미스터리", "가족", "판타지", "범죄"]
    year_list = list(range(2023, current_year + 1))

    # 필터링 여부 확인
    is_filtered = search_query.strip() != '' or selected_year != 'all' or selected_genre != 'all'

    # --- 랭킹 제목 동적 생성 ---
    if search_query:
        ranking_title = f"‘{search_query}’ 검색 결과 Top 10"
    elif selected_year != 'all' and selected_genre != 'all':
        ranking_title = f"{selected_year}년 {selected_genre} 드라마 종합 랭킹 Top 10"
    elif selected_year != 'all':
        ranking_title = f"{selected_year}년 드라마 종합 랭킹 Top 10"
    elif selected_genre != 'all':
        ranking_title = f"{selected_genre} 드라마 종합 랭킹 Top 10"
    elif is_filtered:
        ranking_title = "필터링 결과 드라마 종합 랭킹 Top 10"
    else:
        ranking_title = "전체 드라마 종합 랭킹 Top 10"

    # context
    context = {
        'dramas': display_dramas,
        'top_10_dramas': top_10_dramas,
        'chart_data_json': chart_data_json,  # JSON 문자열 전달
        'ranking_title': ranking_title,
        'year_list': year_list,
        'genre_list': genre_list,
        'selected_year': selected_year,
        'selected_genre': selected_genre,
        'search_query': search_query,
        'is_filtered': is_filtered,
    }

    return render(request, 'dramas/drama_list.html', context)


def drama_detail_view(request, pk):
    drama = Drama.objects.prefetch_related(
        Prefetch('episodes', queryset=EpisodeInfo.objects.order_by('episode_no'))
    ).get(pk=pk)
    return render(request, "dramas/drama_detail.html", {"drama": drama})
