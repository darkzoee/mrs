from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from .decorators import cold_boot
from .models import Music, UserProfile
from .recommend import build_recommend
from .subscribe import build_genre_ids, build_languages

# 当前播放
current_play = None
# 当前推荐
current_recommend = []


# 首页
def home(request):
    return all(request)


@cold_boot
def all(request):
    page_number = request.GET.get('page', 1)
    queryset = Music.objects.all()
    paginator = Paginator(queryset, 10)  # 分页
    musics = paginator.page(page_number)
    context = {
        'musics': musics,
        'user_likes': [],
        'user_dislikes': []
    }
    # 如果登录的首页
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.filter(user=request.user)
        if user_profile.exists():
            user_profile = user_profile.first()  # 用户信息
            context['user_likes'] = user_profile.likes.all()  # 获取用户喜欢或不喜欢的数据
            context['user_dislikes'] = user_profile.dislikes.all()
    return render(request, 'list.html', context)


# 注册
def sign_up(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.add_message(request, messages.ERROR, '该用户已存在！')
        else:
            user_obj = User.objects.create_user(username=username, password=password)
            UserProfile.objects.create(user=user_obj)
            messages.add_message(request, messages.SUCCESS, '注册成功！')
            return HttpResponseRedirect('/sign_in')
    return render(request, 'sign_up.html')


# 登录
def sign_in(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user=user)
            messages.success(request, '登录成功')
            return HttpResponseRedirect('/')
        else:
            messages.add_message(request, messages.ERROR, '用户名或密码错误！')
            return HttpResponseRedirect('/')
    else:
        return render(request, 'sign_in.html')

# 退出登录
@login_required(login_url='/sign_in')
def user_logout(request):
    logout(request)
    messages.info(request, '退出登录')
    return HttpResponseRedirect('/')


@login_required(login_url='/sign_in')
@cold_boot
def recommend(request):
    page_number = request.GET.get('page', 1)

    # -------------------- 推荐 --------------------------
    recommend_set = build_recommend(request, request.user)  # 获取推荐的数据
    # -------------------- 推荐 --------------------------

    paginator = Paginator(recommend_set, 10)  # 分页
    musics = paginator.page(page_number)  # 推荐的音乐
    context = {
        'musics': musics,
        'user_likes': [],
        'user_dislikes': []
    }
    user_profile = UserProfile.objects.filter(user=request.user)
    if user_profile.exists():
        user_profile = user_profile.first()
        context['user_likes'] = user_profile.likes.all()
        context['user_dislikes'] = user_profile.dislikes.all()
    return render(request, 'list.html', context)


# 用户添加喜欢
@login_required(login_url='/sign_in')
def like(request, pk: int):
    user_obj = UserProfile.objects.get(user=request.user)
    music_obj = get_object_or_404(Music.objects.all(), pk=pk)  # 通过id查找歌曲信息
    user_obj.likes.add(music_obj)  # 添加喜欢
    user_obj.dislikes.remove(music_obj)  # 删除不喜欢
    messages.add_message(request, messages.INFO, '已经添加到我喜欢')
    redirect_url = request.GET.get('from', '/')
    if 'action' in request.GET:
        redirect_url += f'&action={request.GET["action"]}'
    return HttpResponseRedirect(redirect_url)


# 用户添加不喜欢
@login_required(login_url='/sign_in')
def dislike(request, pk: int):
    user_obj = UserProfile.objects.get(user=request.user)
    music_obj = get_object_or_404(Music.objects.all(), pk=pk)  # 通过id查找歌曲信息
    user_obj.dislikes.add(music_obj)  # 添加到不喜欢
    user_obj.likes.remove(music_obj)  # 删除喜欢
    messages.add_message(request, messages.INFO, '已经添加到我不喜欢')
    redirect_url = request.GET.get('from', '/')
    if 'action' in request.GET:
        redirect_url += f'&action={request.GET["action"]}'
    return HttpResponseRedirect(redirect_url)


# 播放歌曲
def play(request, pk: int = 0):
    global current_play
    if pk > 0:  # 存在id
        music_obj = Music.objects.filter(pk=pk)
        if music_obj.exists():
            current_play = music_obj.first()
    if current_play is None:
        messages.error(request, '当前没有正在播放的音乐')
        return HttpResponseRedirect('/')
    return render(request, 'play.html', context={
        'music': current_play
    })


# 用户信息
@login_required(login_url='/sign_in')
def user_center(request):
    user_profile = UserProfile.objects.filter(user=request.user)
    if user_profile.exists():
        profile_obj: UserProfile = user_profile.first()
    else:
        messages.error(request, '找不到用户资料，请重新登录')
        logout(request)
        return HttpResponseRedirect('/')
    # 添加个人信息
    if request.method == 'POST':
        genres = request.POST.getlist('genres', '')
        languages = request.POST.getlist('languages', '')
        profile_obj.first_run = False
        if len(genres) > 0:
            profile_obj.genre_subscribe = ','.join(genres)
            profile_obj.save()
            messages.success(request, '修改流派订阅成功！')
        elif not profile_obj.first_run:
            profile_obj.genre_subscribe = ''
            profile_obj.save()
            messages.success(request, '修改流派订阅成功！')
        if len(languages) > 0:
            profile_obj.language_subscribe = ','.join(languages)
            profile_obj.save()
            messages.success(request, '修改语言订阅成功！')
        elif not profile_obj.first_run:
            profile_obj.language_subscribe = ''
            profile_obj.save()
            messages.success(request, '修改语言订阅成功！')
    context = {
        'user_likes': profile_obj.likes.all(),
        'user_dislikes': profile_obj.dislikes.all(),
        'genres': build_genre_ids(),
        'languages': build_languages(),
        'genre_subscribe': profile_obj.genre_subscribe.split(','),
        'language_subscribe': []
    }
    # 去除空字符
    for lang in profile_obj.language_subscribe.split(','):
        lang = lang.strip()
        context['language_subscribe'].append(lang)
    return render(request, 'user.html', context=context)


# 搜索歌曲
def search(request):
    if 'keyword' not in request.GET:
        messages.error(request, '请输入搜索关键词')
        return HttpResponseRedirect('/')
    keyword = request.GET.get('keyword')
    action = request.GET.get('action')
    # 两种方式搜索
    musics = []
    if action == 'song_name':
        musics = Music.objects.filter(song_name__contains=keyword)
    if action == 'artist_name':
        musics = Music.objects.filter(artist_name__contains=keyword)
    messages.info(request, f'搜索关键词：{keyword}，找到 {len(musics)} 首音乐')
    context = {
        'musics': musics,
        'user_likes': [],
        'user_dislikes': []
    }
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.filter(user=request.user)
        if user_profile.exists():
            user_profile = user_profile.first()
            context['user_likes'] = user_profile.likes.all()
            context['user_dislikes'] = user_profile.dislikes.all()
    return render(request, 'list.html', context)
