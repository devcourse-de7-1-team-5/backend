from django.db import models

class Drama(models.Model):
    title = models.CharField(max_length=200)       # 제목
    channel = models.CharField(max_length=50)      # 방송사
    description = models.TextField(null=True, blank=True)  # 줄거리
    start_date = models.DateField()                # 방영일
    end_date = models.DateField(null=True, blank=True)  # 종영일
    img_url = models.URLField(max_length=500, null=True, blank=True) #드라마 이미지
    objects = models.Manager()
    def __str__(self):
        return self.title


class ExternalIDMapping(models.Model):
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE)
    source_name = models.CharField(max_length=50)   # 사이트 이름
    external_id = models.CharField(max_length=100)  # 해당 사이트 고유 ID

    class Meta:
        unique_together = (('source_name', 'external_id'),)

    def __str__(self):
        return f"{self.drama.title} - {self.source_name}: {self.external_id}"
    
class EpisodeInfo(models.Model):
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE,
    related_name="episodes")  # 드라마
    episode_no = models.IntegerField()                          # 회차
    date = models.DateField()                                   # 방영일
    rating = models.FloatField()                                # 시청률
    synopsis = models.TextField(null=True, blank=True)          # 줄거리
    query = models.CharField(max_length=50)                     # 검색 쿼리
    source_url = models.CharField(max_length=200)               # 해당 url
    objects = models.Manager()

    def __str__(self):
        return f"{self.drama.title} + {self.episode_no} + 회차"

class Genre(models.Model):
    drama = models.ForeignKey(Drama, on_delete=models.CASCADE, related_name="genres")   # 장르
    name = models.CharField(max_length=50)                                              # 장르 이름

    def __str__(self):
        return f"{self.drama.title} - {self.name}"