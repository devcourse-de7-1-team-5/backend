from rest_framework import generics

from .models import *
from .serializers import DramaListSerializer, DramaDetailSerializer, EpisodeInfoSerializer
from rest_framework import generics
from django.shortcuts import render
from dramas.models import Drama

class DramaList(generics.ListCreateAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaListSerializer


class DramaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaDetailSerializer

def drama_list_view(request):
    dramas = Drama.objects.all().order_by('start_date')
    return render(request, 'dramas/drama_list.html', {'dramas': dramas})
