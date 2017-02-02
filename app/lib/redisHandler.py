import redis
import properties
import json
from helper import *
import re
from heapq import heappush, heappop, nlargest

# setup the redis storage
user_profile_redis = redis.StrictRedis(
    host=properties.REDIS_HOST, port=properties.REDIS_PORT, db=0)
tweet_redis = redis.StrictRedis(
    host=properties.REDIS_HOST, port=properties.REDIS_PORT, db=1)

# hash the image_id to the owner user_id
image_redis = redis.StrictRedis(
    host=properties.REDIS_HOST, port=properties.REDIS_PORT, db=2)

user_openId_redis = redis.StrictRedis(
    host=properties.REDIS_HOST, port=properties.REDIS_PORT, db=3)

###### FOR user_profile_redis ######


def set_user_profile(user_id, data):
    user_profile_redis.hmset(user_id, data)
    set_openId_for_user(data['openId_user_id'], user_id)


def get_user_profile(user_id):
    data = user_profile_redis.hgetall(user_id)
    # logger.info("get_user_profile: "+string)
    return normaliseReturn(data)


def get_user_profile_by_openId(openId_user_id):
    user_id = get_user_id_from_openId(openId_user_id)
    return get_user_profile(user_id)


def get_all_user_profile():
    data = []
    for key in user_profile_redis.keys():
        if is_redis_main_list_key(key):
            print "getting key %s" % key
            j = get_user_profile(key)
            if j is not None:
                data.append({key: j})
    return normaliseReturn(data)


def is_user_exists(user_id):
    return user_profile_redis.exists(user_id) if is_redis_main_list_key(user_id) else False


def get_user_profile_field(user_id, key):
    return user_profile_redis.hget(user_id, key)


def set_user_profile_field(user_id, key, value):
    user_profile_redis.hset(user_id, key, value)


def get_all_user_id():
    ids = []
    all_users = user_profile_redis.keys()
    for user_id in all_users:
        if is_redis_main_list_key(user_id):
            ids.append(user_id)
    return ids

def search_user(search_key, number_of_result):
    all_users = get_all_user_id()
    possible_users = []
    h = []
    for user_id in all_users:
        name_of_user = get_user_profile_field(user_id, 'name')
        email_of_user = get_user_profile_field(user_id, 'email')
        picture_of_user = get_user_profile_field(user_id, 'picture_url')
        m = re.search(search_key, name_of_user + email_of_user)
        if m:
            user_data = {
                'user_id': user_id,
                'name': name_of_user,
                'email': email_of_user,
                'picture_url': picture_of_user,
            }
            heappush(h, (len(m.group(0)), user_data))
    length = len(h)
    number_of_result = max(0, number_of_result)
    number_of_result = min(length, number_of_result)
    return {
        'results': [heappop(h)[1] for i in range(length-1, max(length-1-number_of_result,-1),-1)],
    }


# def search_user(search):
#     all_users = get_all_user_id()
#     possible_users = []
#     for user_id in all_users:
#         name_of_user = get_user_profile_field(user_id, 'name')
#         email_of_user = get_user_profile_field(user_id, 'email')
#         picture_of_user = get_user_profile_field(user_id, 'picture_url')
#         if re.search(search, name_of_user) or re.search(search, email_of_user):
#             possible_users.append({
#                 'user_id': user_id,
#                 'name': name_of_user,
#                 'email': email_of_user,
#                 'picture_url': picture_of_user,
#             })
#     return {
#         'results': possible_users,
#     }


# only use this to manipulate following followers and tweets

def user_profile_list_add(user_id, field, value):
    # remove all then add to ensure there is only one unique value in the list
    user_profile_list_remove(user_id, field, value)
    user_profile_redis.lpush(
        get_redis_list_name(user_id, field),
        value
    )


def user_profile_list_remove(user_id, field, value):
    user_profile_redis.lrem(
        get_redis_list_name(user_id, field),
        0,  # 0 to remove all from the list
        value
    )


def user_profile_list_count(user_id, field):
    return user_profile_redis.llen(get_redis_list_name(user_id, field))


def user_profile_list_get_all(user_id, field):
    return user_profile_redis.lrange(get_redis_list_name(user_id, field), 0, -1)


###### FOR tweet_redis ######


def set_tweet_json(tweet_id, data):
    tweet_redis.hmset(tweet_id, data)


def get_tweet_json(tweet_id):
    data = tweet_redis.hgetall(tweet_id)
    data['likes'] = get_tweet_likes(tweet_id)
    return normaliseReturn(data)


def get_field_in_tweet(tweet_id, key):
    return tweet_redis.hget(tweet_id, key)


def get_all_tweets_json():
    data = {}
    for key in tweet_redis.keys():
        if is_redis_main_list_key(key):
            j = get_tweet_json(key)
            if j is not None:
                data[key] = j
    return normaliseReturn(data)


def delete_tweet(tweet_id):
    if is_tweet_exists(tweet_id):
        tweet_redis.delete(tweet_id, get_redis_list_name(tweet_id,'likes'))
        return True
    else:
        return False


def is_tweet_exists(tweet_id):
    return tweet_redis.exists(tweet_id)


def like_tweet(user_id, tweet_id):
    unlike_tweet(user_id, tweet_id)
    tweet_redis.lpush(
        get_redis_list_name(tweet_id, 'likes'),
        user_id
    )


def unlike_tweet(user_id, tweet_id):
    tweet_redis.lrem(
        get_redis_list_name(tweet_id, 'likes'),
        0,  # 0 to remove all from the list
        user_id
    )

def get_tweet_likes(tweet_id):
    return tweet_redis.lrange(get_redis_list_name(tweet_id, 'likes'), 0,  -1)






###### FOR image_redis ######


def set_image_owner_id(image_id, user_id):
    image_redis.set(image_id, user_id)


def get_image_owner_id(image_id):
    return image_redis.get(image_id)


###### FOR openID user ######


def set_openId_for_user(openId_user_id, user_id):
    user_openId_redis.set(openId_user_id, user_id)


def get_user_id_from_openId(openId_user_id):
    return user_openId_redis.get(openId_user_id)


# Helper function
def normaliseReturn(data):
    return data if data else None
