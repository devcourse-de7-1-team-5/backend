from django.contrib import admin

from .models import News


# Register your models here.


class NewsAdmin(admin.ModelAdmin):
    readonly_fields = ['date', 'press', 'link']
    fieldsets = [
        ('뉴스 제목', {'fields': ['title']}),
        ('뉴스 내용', {'fields': ['content']}),
        ('작성자', {'fields': ['press']}),
        ('작성일', {'fields': ['date']}),
        ('링크', {'fields': ['link']}),
    ]

    list_display = [
        'title', 'content', 'press'
    ]


admin.site.register(News, NewsAdmin)
