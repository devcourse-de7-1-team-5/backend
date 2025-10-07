from rest_framework import generics

from .models import *
from .serializers import DramaListSerializer, DramaDetailSerializer, EpisodeInfoSerializer
from rest_framework import generics
from django.shortcuts import render
from dramas.models import Drama

from django.http import Http404
import requests
from django.views import View

class DramaList(generics.ListCreateAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaListSerializer


class DramaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaDetailSerializer

def drama_list_view(request):
    dramas = Drama.objects.all().order_by('start_date')
    return render(request, 'dramas/drama_list.html', {'dramas': dramas})

class DramaDetailView(View):
    def get(self, request, pk):
        try:
            res = requests.get(f"http://127.0.0.1:8000/api/dramas/{pk}", timeout=5)
            if res.status_code == 404:
                raise Http404("드라마를 찾을 수 없습니다.")
            res.raise_for_status()  # 200이 아닌 다른 상태코드일 때 예외 발생
            data = res.json()
        except requests.exceptions.RequestException as e:
            # 네트워크 오류, 타임아웃, 500 등
            raise Http404("드라마 정보를 불러올 수 없습니다.") from e
        return render(request, "dramas/drama_detail.html", {"drama": data})