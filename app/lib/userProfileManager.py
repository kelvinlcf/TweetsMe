
from helper import *
from redisHandler import *


def create_user_profile(user_info_json):
    data = {}
    data['id'] = gen_unique_id()
    data['openId_platform'] = 'google'
    data['openId_user_id'] = user_info_json['id']
    data['name'] = user_info_json['name']
    data['family_name'] = user_info_json['family_name']
    data['given_name'] = user_info_json['given_name']
    data['email'] = user_info_json['email']
    # replace https to http
    data['picture_url'] = user_info_json['picture']
    data['lang'] = user_info_json['locale']
    return data




def get_my_profile():
    user_id = get_my_user_id()
    if user_id is not None:
        return get_user_profile(user_id)
    else:
        return None

def is_user_private(user_id):
    profile = get_user_profile(user_id)
    return 'is_private' in profile if profile is not None else False


def is_following(user_id, friend_id):
    # check if the friend_id is in the following array in my profile
    profile = get_user_profile(user_id)
    if profile is not None:
        following = profile['following']
        return friend_id in following
    else:
        return False










def set_user_tweet(user_id, tweet_id):
    if is_user_exists(user_id):
        user_profile_list_add(user_id,'tweets',tweet_id)
        return True
    else:
        return False


def delete_user_tweet(user_id, tweet_id):
    if is_user_exists(user_id):
        user_profile_list_remove(user_id,'tweets',tweet_id)
        return True
    else:
        return False



def set_user_follow(user_id, friend_id):
    if is_user_exists(user_id) and is_user_exists(friend_id) and user_id != friend_id:
        user_profile_list_add(user_id,'following',friend_id)
        user_profile_list_add(friend_id,'followers',user_id)

        return True
    else:
        return False



def set_user_unfollow(user_id, friend_id):
    if is_user_exists(user_id) and is_user_exists(friend_id):
        user_profile_list_remove(user_id,'following',friend_id)
        user_profile_list_remove(friend_id,'followers',user_id)

        return True
    else:
        return False

def get_list_of_tweets_id_from_user(user_id):
    if is_user_exists(user_id):
        return user_profile_list_get_all(user_id,'tweets')
    else:
        return None

def get_all_tweets_json_from_user(user_id):
    list_of_tweet_id = get_list_of_tweets_id_from_user(user_id)
    user_profile = get_user_profile(user_id)
    list_of_tweets = []
    for tweet_id in list_of_tweet_id:
        tweet = get_tweet_json(tweet_id)
        tweet['user_name'] = user_profile['name'];
        tweet['user_picture_url'] = user_profile['picture_url']
        list_of_tweets.append(tweet)
    return list_of_tweets





