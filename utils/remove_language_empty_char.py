import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MusicRecommendSystem.settings")
django.setup()
from music.models import Music

# 去除歌曲语言中的空字符
if __name__ == '__main__':
    music_set = Music.objects.all()
    total = len(music_set)
    for index, music in enumerate(music_set):
        music.language = music.language.replace('\n', '')
        music.save()
        print(f'{index + 1}/{total}: {music.song_name}')
