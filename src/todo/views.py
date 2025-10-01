from rest_framework import generics

from .models import *
from .serializers import DramaListSerializer, DramaDetailSerializer, EpisodeInfoSerializer

class DramaList(generics.ListCreateAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaListSerializer


class DramaDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Drama.objects.all()
    serializer_class = DramaDetailSerializer
