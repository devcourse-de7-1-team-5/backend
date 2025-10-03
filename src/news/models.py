from django.contrib.auth.models import User
from django.db import models

from dramas.models import EpisodeInfo


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    press = models.CharField(max_length=100, null=True, blank=True)
    link = models.URLField(max_length=500, null=True, blank=True)
    drama_ep = models.ForeignKey(
        EpisodeInfo, on_delete=models.CASCADE,
        related_name='drama_news', null=True,
        blank=True
    )

    objects = models.Manager()

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        constraints = [
            models.UniqueConstraint(
                fields=['link', 'drama_ep'],
                name='unique_link_drama_ep'
            )
        ]

    def __str__(self):
        return self.title
