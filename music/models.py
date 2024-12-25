from django.contrib.auth.models import User
from django.db import models


# 用户信息
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    likes = models.ManyToManyField('Music', blank=True, related_name='like_users')
    dislikes = models.ManyToManyField('Music', blank=True, related_name='dislike_users')
    first_run = models.BooleanField('是否第一次运行,执行冷启动策略', default=True)
    genre_subscribe = models.TextField('流派订阅', blank=True)
    language_subscribe = models.TextField('语言订阅', blank=True)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name


# 音乐
class Music(models.Model):
    song_name = models.CharField('歌曲名称', max_length=1000)
    song_length = models.IntegerField('歌曲长度 单位为ms')
    genre_ids = models.CharField('歌曲流派', max_length=100)
    artist_name = models.CharField('歌手', max_length=1000)
    composer = models.CharField('作曲', max_length=1000)
    lyricist = models.CharField('作词', max_length=1000)
    language = models.CharField('语种', max_length=20)
    url = models.CharField('歌曲链接', max_length=1000, default="https://m701.music.126.net/20240301234259/3c4c6553837086cd21eb6013475d9d05/jdymusic/obj/wo3DlMOGwrbDjj7DisKw/27978919250/663c/4088/7b7a/0c48207cb013f953f46fe2da7dd7f803.mp3")

    def __str__(self):
        return self.song_name

    class Meta:
        verbose_name = '音乐信息'
        verbose_name_plural = verbose_name
