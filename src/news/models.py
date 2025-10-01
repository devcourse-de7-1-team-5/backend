from django.contrib.auth.models import User
from django.db import models


class News(models.Model):
    # TODO: Drama or DramaEpisode와 ForeignKey로 연결

    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    press = models.CharField(max_length=100, null=True, blank=True)
    link = models.URLField(max_length=500, null=True, blank=True, unique=True)
    objects = models.Manager()

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"

    def __str__(self):
        return self.title
