from django.contrib import admin
from .models import Drama, EpisodeInfo


# Register your models here.
class DramaAdmin(admin.ModelAdmin):
    list_display =(
        'title',
        'channel',
        'start_date',
        'end_date'
    )
    search_fields=['title']
    search_help_text = '드라마 제목으로 검색 가능합니다.'

                    
class EpisodeInfoAdmin(admin.ModelAdmin):
    list_display = ('drama', 'episode_no', 'date', 'rating')
    search_fields =['episode_no']
    search_help_text = '드라마 회차로 검색 가능합니다.'

admin.site.register(Drama, DramaAdmin)
admin.site.register(EpisodeInfo, EpisodeInfoAdmin)
