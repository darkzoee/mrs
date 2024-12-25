from django.contrib import admin

from .models import Music, UserProfile

admin.site.site_title = "音乐推荐系统后台管理系统"
admin.site.site_header = "音乐推荐系统-后台管理系统"
admin.site.index_title = "音乐推荐系统"


@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    # 设置列表中显示的字段
    list_display = ['id', 'song_name', 'song_length', 'genre_ids', 'artist_name', 'composer', 'lyricist', 'language',
                    'url']
    # 搜索
    search_fields = ['song_name', 'artist_name', 'composer', 'language']
    # 过滤
    list_filter = ['language']
    # 设置每页现实的数据量
    list_per_page = 12
    # 设置排序
    ordering = ['id']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'user_id', 'user', 'first_run', 'genre_subscribe', 'language_subscribe']
    # 搜索
    search_fields = ['user']
    # 过滤
    list_filter = ['genre_subscribe', 'language_subscribe']
    # 设置每页现实的数据量
    list_per_page = 12
    # 设置排序
    ordering = ['pk']

    def user_id(self, obj: UserProfile):
        return obj.user.id
