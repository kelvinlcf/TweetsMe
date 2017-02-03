#!/usr/bin/python
import logging
from flask import Flask, session, redirect, url_for, request, render_template, Response, make_response, send_file
import properties
import sys
from lib import oAuth2
from lib.s3Handler import s3_put, s3_get, s3_delete
from uuid import uuid4
import json
import requests
import httplib2
import apiclient
from lib.helper import *
from time import time
from time import sleep
import base64
from lib.redisHandler import *
from lib.mimetypeFilter import *
from lib.userProfileManager import *
from operator import itemgetter

# ENV for development
APP_HOST='0.0.0.0'

app = Flask(__name__)
app.secret_key = str(uuid4())
app.config.update(SEND_FILE_MAX_AGE_DEFAULT=0)

###### setup the logger ######
# logging.basicConfig(filename=properties.LOG_FILE, level=logging.DEBUG)
logger = logging.getLogger()

logger.setLevel(properties.LOG_LEVEL)
# create console handler and set level to debug
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.NOTSET)
# create formatter
# formatter = logging.Formatter('%(asctime)19s | %(name)10s | %(levelname)7s | %(module)9s | %(funcName)10s | %(message)s')
formatter = logging.Formatter('%(asctime)19s | %(levelname)7s | %(funcName)24s | %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

debug = False


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.route('/')
def index():
    return send_file("templates/index.html")

@app.route('/unauthorized_login')
def unauthorized_login_page():
    return send_file("templates/unauthorized_login_page.html")

@app.route('/oAuth2Callback')
def oauth2_callback():
    if 'code' not in request.args:
        url = oAuth2.get_authorize_url()
        logger.info("Redirecting to "+url)
        return redirect(url)
    else:
        auth_code = request.args.get('code')
        # exchanging auth code with token
        user_info_json = oAuth2.exchange_credentials(auth_code)        

        if not hosted_domain_verification(user_info_json):
            return redirect(url_for('unauthorized_login_page',_external=True))

        # store the user info to session
        session['user_info'] = user_info_json

        # make a new user profile if the user is no in the system before
        openId_user_id = user_info_json['id']
        logger.info("User login with google openId: "+openId_user_id)
        user_profile = get_user_profile_by_openId(openId_user_id)
        if user_profile is None:
            logger.info("New user, enter create new user profile process")
            data = create_user_profile(user_info_json)
            set_user_profile(data['id'],data)
        else:
            logger.info("Existing user")

        logger.info("Redirecting to index page")
        return redirect(url_for('index',_external=True))

# search user_id
@app.route(build_api_path('/user/search/<search_key>'), methods=['GET'])
def api_search_user_by_name(search_key):
    if auth():
        result = search_user(search_key, properties.MAX_SEARCH_RESULT)
        return make_response(dict_to_json(result),200)
    else:
        return make_message_response("not authorized", 401)



# Post a new tweets
@app.route(build_api_path('/tweets/post'), methods=['POST'])
def api_post_tweets():
    if auth():
        # pull the current user information from the credentials
        user_id = get_my_user_id()
        logger.info("userid: "+user_id)

        if not is_user_exists(user_id):
            logger.warn("User does not exists in system")
            return make_message_response("User does not exists in system", 400)

        if len(request.values['message']) > properties.MAX_MESSAGE_LENGTH:
            logger.info("message length: "+ str(len(request.values['message'])))
            return make_message_response('message length exceeded the system limit', 400)

        if request.values['font'] is None or request.values['color'] is None:
            return make_message_response('post tweet request without font or color',400)
        elif not validate_color(request.values['color']):
            return make_message_response('invalid color',400)

        # store the media to s3
        image_id = None
        image = None
        if 'image' in request.files:
            logger.info("Image found in request.files")
            image = request.files['image']
            if mimetypeFilter(image.content_type):
                image_id = gen_unique_id()
                s3_put(image_id,image)
                set_image_owner_id(image_id, user_id)
                logger.info("Image processed: [image_id:%s]" % image_id)
            else:
                logger.warn("Invalid image content-type: "+ image.content_type);
                return make_message_response('Invalid image content-type', 400)
        else:
            logger.info("No image found in request.files")



        # generate unique id for this tweets
        tweet_id = gen_unique_id()
        # build the post data dictionary
        post_data = {
            'tweet_id': tweet_id,
            'message': request.values['message'],
            'user_id': user_id,
            'timestamp': time(),
            'font': request.values['font'],
            'color': request.values['color'],
        }
        if image_id is not None:
            post_data['image_id'] = image_id

        # store the post in the tweets db
        set_tweet_json(tweet_id, post_data)

        # store the post in the user profile
        set_user_tweet(user_id, tweet_id)

        # build the json for response
        resp_data = {
            'tweet_id': tweet_id,
            'user_id': user_id,
            'timestamp': time()
        }
        if image_id is not None:
            resp_data['image_id'] = image_id
        return make_response(dict_to_json(resp_data), 200)
    else:
        return make_message_response("not authorized", 401)


# remove the tweet from the tweet db and the user profile of the owner of the tweet
@app.route(build_api_path('/tweets/<tweet_id>'), methods=['DELETE'])
def api_delete_tweets(tweet_id):
    if auth():
        if is_tweet_exists(tweet_id):
            user_id = get_field_in_tweet(tweet_id,'user_id')
            if user_id != get_my_user_id():
                return make_message_response('Invalid delete request, user do you own the post', 400)
            # logger.info("Delete tweet: [userid: %s]",user_id)
            if delete_tweet(tweet_id) and delete_user_tweet(user_id,tweet_id):
                return make_message_response('success',200)
            else:
                return make_message_response('Fail to delete tweet with id: '+tweet_id, 400)
        else:
            return make_message_response('Tweet does not exists', 400)
    else:
        return make_message_response("not authorized", 401)



# get all the news feed from user I followed up to a certain time range
@app.route(build_api_path('/user/news_feed'), methods=['GET'])
def api_get_user_news_feed():
    if auth():
        from_tweet_id = request.args.get('from_tweet_id')
        limit = request.args.get('limit')
        feed = get_my_news_feed(from_tweet_id, limit)
        if feed is None:
            return make_message_response('invalid request', 400)
        else:
            return make_response(dict_to_json(feed),200)
    else:
        return make_message_response("not authorized", 401)




# get all the tweets from a particular user
@app.route(build_api_path('/user/tweets'), methods=['GET'])
def api_get_tweets_from_current_user():
    return api_get_tweets_from_user(get_my_user_id())



# get all the tweets from a particular user
@app.route(build_api_path('/user/<target_user_id>/tweets'), methods=['GET'])
def api_get_tweets_from_user(target_user_id):
    if auth():
        if is_user_exists(target_user_id):
            list_of_tweets = get_all_tweets_json_from_user(target_user_id)
            list_of_tweets.sort(key=extract_timestamp, reverse=True)
            from_tweet_id = request.args.get('from_tweet_id')
            limit = request.args.get('limit')
            data = {}
            if (limit is not None):
                try:
                    limit = int(limit)
                except ValueError:
                    return make_message_response("invalid request", 400)
                if  limit >= 0 and from_tweet_id is not None and is_tweet_exists(from_tweet_id):
                    for i in range(0,len(list_of_tweets)):
                        if list_of_tweets[i]['tweet_id'] == from_tweet_id:
                            originalLength = len(list_of_tweets)
                            list_of_tweets = list_of_tweets[i+1:i+1+limit]
                            data['from_tweet_id'] = from_tweet_id
                            data['count'] = min(limit,originalLength-i-1)
                            break;
                else:
                    list_of_tweets = list_of_tweets[:limit]

            data['tweets'] = list_of_tweets
            return make_response(dict_to_json(data),200)
        else:
            return make_message_response("user does not exists", 400)
    else:
        return make_message_response("not authorized", 401)



@app.route(build_api_path('/media/image/<image_id>'), methods=['GET'])
def api_get_image(image_id):
    # auth the current user
    if auth():
        # get my user_id
        user_id = get_my_user_id()
        logger.info("loading with user id: "+user_id)
        # check if the user_id belongs to one of the user
        return get_image_response_by_id(image_id)
    else:
        # return redirect(url_for('index',_external=True))
        return make_message_response("not authorized", 401)


# return the user profile of the user in this session
@app.route(build_api_path('/user/profile'), methods=['GET'])
def api_get_my_user_profile():
    if auth():
        return api_get_user_profile_aux(get_my_user_id());
    else:
        return make_message_response("not authorized", 401)


# return the user profile of a particular user with user_id
@app.route(build_api_path('/user/<user_id>/profile'), methods=['GET'])
def api_get_user_profile(user_id):
    if auth():
        return api_get_user_profile_aux(user_id);
    else:
        return make_message_response("not authorized", 401)


def api_get_user_profile_aux(user_id):
    if is_user_exists(user_id):
        profile = get_user_profile(user_id)
        followers = user_profile_list_get_all(user_id,'followers')
        following = user_profile_list_get_all(user_id,'following')
        tweets = user_profile_list_get_all(user_id,'tweets')

        profile['followers'] = followers
        profile['following'] = following
        profile['tweets'] = tweets

        if profile is not None:
            return make_response(dict_to_json(profile), 200)
        else:
            return make_message_response('user profile does not exist',400)
    else:
        return make_message_response('user does not exists', 400)


# set the current user to follow the user with user_id
@app.route(build_api_path('/follow/<friend_id>'), methods=['PUT'])
def api_follow_user(friend_id):
    if auth():
        user_id = get_my_user_id()
        if is_user_exists(user_id) and is_user_exists(friend_id):
            success = set_user_follow(user_id, friend_id)
            if success:
                following = {
                    'following': user_profile_list_get_all(user_id,'following'),
                }
                return make_response(dict_to_json(following), 200)
            else:
                return make_message_response('unable to follow user with id: '+friend_id, 400)
        else:
            # user does not exist
            return make_message_response('User does not exists', 400)
    else:
        return make_message_response("not authorized", 401)

# set the current user to unfolloow the user with user_id
@app.route(build_api_path('/unfollow/<friend_id>'), methods=['PUT'])
def api_unfollow_user(friend_id):
    if auth():
        user_id = get_my_user_id()
        if is_user_exists(user_id) and is_user_exists(friend_id):
            success = set_user_unfollow(user_id, friend_id)
            if success:
                following = {
                    'following': user_profile_list_get_all(user_id,'following'),
                }
                return make_response(dict_to_json(following), 200)
            else:
                return make_message_response('unable to follow user with id: '+friend_id, 400)
        else:
            # user does not exist
            return make_message_response('User does not exists', 400)
    else:
        return make_message_response("not authorized", 401)

# get all the follower of the current user
@app.route(build_api_path('/user/<user_id>/followers'), methods=['GET'])
def api_get_followers(user_id):
    if auth():
        if is_user_exists(user_id):
            all_followers = []
            all_followers_id = user_profile_list_get_all(user_id,'followers')
            for user_id in all_followers_id:
                name_of_user = get_user_profile_field(user_id,'name')
                email_of_user = get_user_profile_field(user_id,'email')
                picture_of_user = get_user_profile_field(user_id,'picture_url')
                all_followers.append({
                    'user_id': user_id,
                    'name': name_of_user,
                    'email': email_of_user,
                    'picture_url': picture_of_user,
                })
            return make_response(dict_to_json({'results':all_followers}),200)
        else:
            # user does not exist
            return make_message_response('User does not exists', 400)
    else:
        return make_message_response("not authorized", 401)


# get all the following user of the current user
@app.route(build_api_path('/user/<user_id>/following'), methods=['GET'])
def api_get_following(user_id):
    if auth():
        if is_user_exists(user_id):
            all_following = []
            all_following_id = user_profile_list_get_all(user_id,'following')
            for user_id in all_following_id:
                name_of_user = get_user_profile_field(user_id,'name')
                email_of_user = get_user_profile_field(user_id,'email')
                picture_of_user = get_user_profile_field(user_id,'picture_url')
                all_following.append({
                    'user_id': user_id,
                    'name': name_of_user,
                    'email': email_of_user,
                    'picture_url': picture_of_user,
                })
            return make_response(dict_to_json({'results':all_following}),200)
        else:
            # user does not exist
            return make_message_response('User does not exists', 400)
    else:
        return make_message_response("not authorized", 401)

@app.route(build_api_path('/tweets/<tweet_id>/like'), methods=['PUT'])
def api_like_tweet(tweet_id):
    if auth():
        if is_tweet_exists(tweet_id):
            user_id = get_my_user_id()
            like_tweet(user_id,tweet_id)
            data = {
                'result': 'success',
                'likes': get_tweet_likes(tweet_id),
                'tweet_id': tweet_id,
            }
            return make_response(dict_to_json(data), 200)
        else:
            return make_message_response('Tweet does not exists', 400)
    else:
        return make_message_response("not authorized", 401)


@app.route(build_api_path('/tweets/<tweet_id>/unlike'), methods=['PUT'])
def api_unlike_tweet(tweet_id):
    if auth():
        if is_tweet_exists(tweet_id):
            user_id = get_my_user_id()
            unlike_tweet(user_id,tweet_id)
            data = {
                'result': 'success',
                'likes': get_tweet_likes(tweet_id),
                'tweet_id': tweet_id,
            }
            return make_response(dict_to_json(data), 200)
        else:
            return make_message_response('Tweet does not exists', 400)
    else:
        return make_message_response("not authorized", 401)

@app.route(build_api_path('/user/logout'), methods=['PUT'])
def api_logout():
    if auth():
        clear_user_session()
        return make_message_response('success', 200)
    else:
        return make_message_response('not authorized', 401)


# will be call when an error happens in flask
# custom 404 page will be display
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404









###### END POINT FOR TESTING ######

@app.route('/credentials')
def api_credentials():
    if app.testing:
        data = json.loads(session['credentials'])
        print json.dumps(data,indent=2, separators=(',',': '))
        return "credentials"
    else:
        return redirect(url_for('oauth2_callback',_external=True)) 

@app.route('/userinfo')
def api_userinfo():
    if app.testing:
        data = get_user_info()
        print json.dumps(data,indent=2, separators=(',',': '))
        return "user_info"
    else:
        return redirect(url_for('oauth2_callback',_external=True))

@app.route('/user_profile_redis')
def get_user_profile_redis():
    if app.testing:
        data = [{'all user_id': user_profile_redis.keys()}]
        all_profile = get_all_user_profile()
        if all_profile is not None:
            data.append(all_profile)
        return make_response(dict_to_json(data))

@app.route('/tweet_redis')
def get_tweet_redis():
    if app.testing:
        data = get_all_tweets_json()
        if data is None:
            data = []
        return make_response(dict_to_json(data))

@app.route('/app_setting')
def api_app_setting():
    if app.testing:
        data = {
            'debug': app.debug
        }
        return make_response(dict_to_json(data))








###### HELPER FUNCTIONS ######
# def auth():
#     credentials = oAuth2.get_credentials()
#     if credentials is not None and not credentials.access_token_expired:
#         logger.debug("AUTH: OK")
#         return True
#     else:
#         logger.debug("AUTH: FAIL")
#         return False

def auth():
    user_info = get_user_info()
    if user_info is not None:
        return True
    else:
        return False



def get_user_info():
    if 'user_info' in session:
        return session['user_info']
    else:
        return None

def get_my_user_id():
    user_id = None
    # only works if login with google openID Connect
    # as we store the user_info form openID Connect to flask session
    user_info = get_user_info()
    openId_user_id = user_info['id']
    user_id = get_user_id_from_openId(openId_user_id)
    return user_id


# Pull the image by image_id
# return an flask response
def get_image_response_by_id(image_id):
    img_obj = s3_get(image_id)
    response = make_response(img_obj['Body'].read())
    logger.info(img_obj['ContentType'])
    response.headers['Content-Type'] = img_obj['ContentType']
    # NOTES: turn this on if we need attachment
    # response.headers['Content-Disposition'] = 'attachment; filename=img.jpg'
    return response



def make_message_response(message, status_code):
    return make_response(dict_to_json({
        'message': message,
    }), status_code)



def get_my_news_feed(from_tweet_id=None, limit=None):
    # for all of my followers
    # get all their news feed
    # sort it by time
    all_tweets = []
    user_id = get_my_user_id()
    news_feed_users = user_profile_list_get_all(user_id,'following')
    news_feed_users.append(user_id)

    for f in news_feed_users:
        tweets = get_all_tweets_json_from_user(f)
        all_tweets.extend(tweets)

    sorted_all_tweets = sorted(all_tweets, key=itemgetter('timestamp'), reverse=True)

    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            return None
        if limit < 0:
            return None
        if from_tweet_id is not None:
            logger.debug("from_tweet_id: "+from_tweet_id)

            for i in range(0,len(sorted_all_tweets)):
                if sorted_all_tweets[i]['tweet_id'] == from_tweet_id:
                    sorted_all_tweets = sorted_all_tweets[i+1:i+1+limit]
                    break
        else:
            logger.debug('no from_tweet_id')
            sorted_all_tweets = sorted_all_tweets[:limit]
    return sorted_all_tweets

def clear_user_session():
    # if 'credentials' in session:
    #     del session['credentials']
    if 'user_info' in session:
        del session['user_info']




if __name__ == '__main__':
    app.run(debug=False, host=APP_HOST)
