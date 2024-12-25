from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from music import views

# 主路由
urlpatterns = [
    path('grappelli/', include('grappelli.urls')),  # 后台
    path('admin/', admin.site.urls),  # 后台
    path('', views.home),  # 首页
    path('recommend', views.recommend),  # 推荐
    path('sign_in', views.sign_in),  # 登录
    path('sign_up', views.sign_up),  # 注册
    path('logout', views.user_logout),  # 退出
    path('like/<int:pk>', views.like),  # 喜欢
    path('dislike/<int:pk>', views.dislike),  # 不喜欢
    path('play', views.play),  # 播放
    path('play/<int:pk>', views.play),  # 播放
    path('user', views.user_center),  # 用户中心
    path('search', views.search),  # 搜索
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
