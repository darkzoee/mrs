import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MusicRecommendSystem.settings")
django.setup()
from music.models import Music
from music.subscribe import genre_labels, language_labels

# 处理流派和语言数据存入数据库（id转换为中文）
if __name__ == '__main__':
    music_set = Music.objects.all()
    total = len(music_set)
    for index, music in enumerate(music_set):
        music.language = language_labels.get(music.language, music.language)
        music.genre_ids = genre_labels.get(music.genre_ids, music.genre_ids)
        music.save()
        print(f'{index + 1}/{total}: {music.song_name}')
