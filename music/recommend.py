import os

import django
import pandas as pd
from django.contrib import messages
from django.http import HttpRequest
from surprise import Dataset, Reader, Prediction
from surprise import SVD

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MusicRecommendSystem.settings")
django.setup()

from django.contrib.auth.models import User
from music.models import UserProfile, Music

current_request = None

'''
SVD（Singular Value Decomposition）是一种基于矩阵分解的算法，通常用于推荐系统中的评分预测。
在Surprise库中的SVD算法采用了隐式反馈数据来进行预测。
SVD算法的基本原理是将用户-物品评分矩阵分解为多个低秩矩阵的乘积，从而捕捉用户和物品的隐含特征。
SVD算法的原理步骤：
1. 隐含特征表示：SVD将用户-物品评分矩阵分解为三个矩阵的乘积，即U、S和V^T。
其中，U矩阵表示用户的隐含特征，S矩阵为奇异值矩阵，V^T矩阵表示物品的隐含特征。
2. 降维处理：奇异值矩阵S中的奇异值按降序排列，取前k个奇异值，可以实现对矩阵的降维处理。这样可以减少计算量，并聚焦于较重要的特征。
3. 重构评分矩阵：将U、S和V^T的前k列分别取出，构成降维后的矩阵。然后将它们相乘，再根据需要减去均值，即可得到重构的评分矩阵。
4. 预测评分：利用重构的评分矩阵，可以预测用户对未评分物品的评分。
预测评分的方法可以是简单的矩阵相乘，也可以加入一些调整因子如全局偏差、用户偏差和物品偏差等。
通过以上步骤，SVD算法可以在用户-物品评分矩阵的基础上，对未评分物品进行预测。
预测的评分值可以用于推荐系统中的排序和推荐过程。

需要注意的是，SVD算法在处理大规模数据时可能会面临内存和计算效率的问题。
'''


# 获取数据库中所有用户数据
def build_df():
    data = []
    for user_profile in UserProfile.objects.all():  # 获取所有的用户信息
        for like_music in user_profile.likes.all():  # 循环获取所有用户喜欢的歌曲
            data.append([user_profile.user.id, like_music.pk, 1])  # 保存数据data = [[1,1,1],]
        for dislike_music in user_profile.dislikes.all():  # 循环获取所有用户不喜欢的歌曲
            data.append([user_profile.user.id, dislike_music.pk, 0])  # 保存数据data = [[1,2,0]]

    return pd.DataFrame(data, columns=['userID', 'itemID', 'rating'])  # 存储格式


'''
userID  itemID  rating
    2       1       1
    2       4       1
    2       9       1
    2       2       0
    2       3       0
    ...     ...     ...
'''


# 根据用户的评分数据来构建预测模型，并返回一组推荐的音乐列表
def build_predictions(df: pd.DataFrame, user: User):
    userId = user.id  # 获取用户的ID
    profile = UserProfile.objects.filter(user=user)  # 查找用户的个人资料信息
    if profile.exists():
        profile_obj: UserProfile = profile.first()
    else:
        return []
    # print("profile", profile)  # <QuerySet [<UserProfile: wyucnk>]>
    # 使用Surprise库中的Reader和Dataset类来构建评分数据集
    # 指定评分范围为0到1之间的连续值
    reader = Reader(rating_scale=(0, 1))
    # 将数据加载到评分数据集中
    data = Dataset.load_from_df(df[['userID', 'itemID', 'rating']], reader)
    # 使用评分数据集构建训练集
    trainset = data.build_full_trainset()
    # 创建一个SVD算法对象
    algo = SVD()
    # 通过algo.fit(trainset)方法训练算法，将训练集数据拟合到算法中
    # 训练完毕
    algo.fit(trainset)

    # 取出当前所有有人评分过的歌曲，并去重
    subsets = df[['itemID']].drop_duplicates()
    # print('subsets', subsets)
    '''
    itemID
       1
       4
       9
       2
       3
       ...
    '''
    # 测试集
    testset = []
    # 从评分数据中提取出所有被评分过的音乐，并将其作为测试集
    for row in subsets.iterrows():
        # 测试集中的评分值被设置为0，因为我们只是想预测用户是否会喜欢这些音乐，而不关心具体的评分值。
        testset.append([userId, row[1].values[0], 0])
    # print('testset', testset)
    '''
     [[4, 1, 0], [4, 4, 0], [4, 9, 0], [4, 2, 0], [4, 3, 0], [4, 5, 0], [4, 19, 0], [4, 21, 0], [4, 63, 0], 
    '''
    # 用训练好的算法对测试集进行预测，返回一个包含预测结果的列表
    predictions = algo.test(testset, verbose=True)
    # print('predictions', predictions)
    '''
    预测结果：用户id为4的用户对物品id为1的物品的评分预测为0.8837081860340208
    r_ui表示实际评分为0，est表示预测评分为0.8837081860340208。
    details中的was_impossible为False表示该预测能够完成，不是不可能的预测。
    [Prediction(uid=4, iid=1, r_ui=0, est=0.8837081860340208, details={'was_impossible': False}), 
    '''
    result_set = []
    user_like = profile_obj.likes.all()  # 当前用户喜欢的
    user_dislike = profile_obj.dislikes.all()  # 当前用户不喜欢的
    # 遍历所有预测结果
    for item in predictions:
        prediction: Prediction = item
        # 对于预测评分高于0.99的音乐，它从数据库中获取相应的音乐对象
        if prediction.est > 0.99:
            music = Music.objects.get(pk=prediction.iid)
            # 检查是否用户已经喜欢或不喜欢该音乐，如果是，则跳过该音乐。
            if music in user_like:
                continue
            if music in user_dislike:
                continue
            result_set.append(music)
    if len(result_set) == 0:
        messages.error(current_request, '你听的歌太少了，多听点歌再来吧~')
    # print('result_set', result_set)
    '''
     [<Music: 愛我的資格>, <Music: 裂縫中的陽光 (Before Sunrise)>, <Music: PLAYING WITH FIRE>, 
    '''
    return result_set


# 获取用户流派推荐
def build_genre_predictions(user: User):
    predictions = []
    profile = UserProfile.objects.filter(user=user)  # 用户信息
    if profile.exists():
        profile_obj: UserProfile = profile.first()
    else:
        return predictions

    genre_subscribe = profile_obj.genre_subscribe.split(',')  # 获取用户订阅的流派
    user_like = profile_obj.likes.all()  # 获取用户喜欢的音乐
    user_dislike = profile_obj.dislikes.all()  # 获取用户不喜欢的音乐

    # 查找遍历用户喜欢流派的所有音乐
    for music in Music.objects.filter(genre_ids__in=genre_subscribe):
        if music in user_like:
            continue
        if music in user_dislike:
            continue
        predictions.append(music)

    return predictions


# 构建语言推荐
def build_language_predictions(user: User):
    predictions = []
    profile = UserProfile.objects.filter(user=user)
    if profile.exists():
        profile_obj: UserProfile = profile.first()
    else:
        return predictions

    language_subscribe = profile_obj.language_subscribe.split(',')  # 获取用户喜欢的语言
    user_like = profile_obj.likes.all()
    user_dislike = profile_obj.dislikes.all()

    for music in Music.objects.filter(language__in=language_subscribe):
        if music in user_like:
            continue
        if music in user_dislike:
            continue
        predictions.append(music)

    return predictions


# 构建推荐
def build_recommend(request: HttpRequest, user: User):
    global current_request
    current_request = request
    predictions = []
    predictions.extend(build_predictions(build_df(), user))  # 算法预测
    if not predictions:
        predictions.extend(build_genre_predictions(user))  # 流派推荐
        predictions.extend(build_language_predictions(user))  # 语言推荐
    return predictions


if __name__ == '__main__':
    # print(build_df())  # 获取用户数据
    print(build_predictions(build_df(), User.objects.get(pk=4)))  # 算法推荐
    print(build_genre_predictions(User.objects.get(pk=4)))  # 流派推荐
    print(build_language_predictions(User.objects.get(pk=4)))  # 语言推荐
