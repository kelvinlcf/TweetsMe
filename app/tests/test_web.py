import sys
sys.path.append('..')
from lib import s3Handler
from lib import oAuth2
import lib
import redis
from mock import Mock
import unittest
import web
import properties
import json


# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger()
client_secret_path = '../'+properties.CLIENT_SECRET_FILE

apiBase = "/api/v1.0"
my_user_id   = '8c29eef6-045d-4c1d-8153-fc3f46de496f'
my_friend_id = '8321i1i13kj4h1jk23k412h3k4h1jk321k1k'

my_profile = {
                'id' : my_user_id,
                'openId_platform': 'google',
                'openId_user_id': '116130720641978651603',
                'name': 'kelvin li',
                'family_name' : 'li',
                'given_name': 'kelvin',
                'email' : 'kelvin.li@g.hde.co.jp',
                'picture_url' : 'https://lh3.googleusercontent.com/-5Dla7noy4J8/AAAAAAAAAAI/AAAAAAAAAAo/NHrffFe1ZKo/photo.jpg',
                'lang' : 'en'
            }

my_friend_profile = {
                'id' : my_friend_id,
                'openId_platform': 'google',
                'openId_user_id': '216138753641978651603',
                'name': 'peter he',
                'family_name' : 'he',
                'given_name': 'peter',
                'email' : 'peter.he@g.hde.co.jp',
                'picture_url' : 'https://lh3.googleusercontent.com/-5Dla7noy4J8/AAAAAAAAAAI/AAAAAAAAAAo/NHrffFe1ZKo/photo.jpg',
                'lang' : 'en'
            }



class TestWeb(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.app = web.app.test_client()
        web.app.testing = True;
        self.log_me_in()


    @classmethod
    def setup_test_env(self,user_id, user_profile):
        credentials_mock = Mock(
            return_value={
                "family_name": user_profile['family_name'],
                "name": user_profile['name'],
                "picture": "https://lh3.googleusercontent.com/-5Dla7noy4J8/AAAAAAAAAAI/AAAAAAAAAAo/NHrffFe1ZKo/photo.jpg",
                "locale": "en",
                "email": user_profile['email'],
                "given_name": user_profile['given_name'],
                "id": user_profile['openId_user_id'],
                "hd": "g.hde.co.jp",
            })
        oAuth2.exchange_credentials = credentials_mock
        web.get_my_user_id = Mock(
            return_value=user_id
            )
        web.create_user_profile = Mock(
            return_value=user_profile)




    def test_login(self):
        recv = self.login()
        assert recv.status_code == 302
        assert 'http://localhost/' == recv.location



    def test_index(self):
        recv = self.app.get('/')
        assert recv.status_code == 200

    def test_api_post_tweet(self):
        self.login()
        recv = self.app.post(apiBase+'/tweets/post',
            data = dict(
                image=open ('img/abc.jpg','rb'),
                message="hello world",
                font='',
                color=''
            ),
            follow_redirects=True, content_type='multipart/form-data')


        recv_json = json.loads(recv.data)
        all_tweets = web.get_all_tweets_json()
        # self.print_json(all_tweets)

        assert recv_json['tweet_id'] in all_tweets
        assert recv_json['user_id'] == my_user_id
        assert recv.status_code == 200

        return recv_json

    def test_api_delete_tweet(self):
        self.login()

        post_json = self.test_api_post_tweet()

        recv = self.app.delete(apiBase+'/tweets/'+post_json['tweet_id'])

        all_tweets = web.get_all_tweets_json()
        if all_tweets is None:
            all_tweets = {}
        # self.print_json(post_json)
        # self.print_json(all_tweets)
        assert recv.status_code == 200
        assert post_json['tweet_id'] not in all_tweets
        assert json.loads(recv.data)['message'] == 'success'


    # verify that all the tweets we get for the current user actually come from the current user
    def test_api_get_tweets_from_user(self):
        self.login()
        post_json = self.test_api_post_tweet()

        recv = self.app.get(apiBase+'/user/tweets')
        recv_json = json.loads(recv.data)

        # self.print_json(recv_json)

        for tweet in recv_json['tweets']:
            # print "checking "+tweet['tweet_id']
            assert tweet['user_id'] == my_user_id


    def test_api_post_message_max_length(self):
        self.login()
        message = "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"+ \
                  "I am testing the system"
        recv = self.app.post(apiBase+'/tweets/post',
            data = dict(
                image=open ('img/abc.jpg','rb'),
                message=message,
                font=''
            ),
            follow_redirects=True, content_type='multipart/form-data')

        recv_json = json.loads(recv.data)
        assert recv_json['message'] == "message length exceeded the system limit"
        assert recv.status_code == 400


    def test_api_get_my_user_profile(self):
        self.login()
        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)

        assert recv_json['id'] == my_profile['id']
        assert recv_json['family_name'] == my_profile['family_name']
        assert recv_json['given_name'] == my_profile['given_name']
        assert recv_json['name'] == my_profile['name']
        assert recv_json['openId_user_id'] == my_profile['openId_user_id']
        assert recv_json['picture_url'] == my_profile['picture_url']
        assert 'tweets' in recv_json

    def test_follow_friend(self):
        # login with my account
        self.log_me_in()

        # login with my friend account
        self.log_friend_in()

        # login with my account
        self.log_me_in()

        # with my account, follow my friend
        recv = self.app.put(apiBase+'/follow/'+my_friend_id)
        assert recv.status_code == 200

        # check if the following record is in my account
        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        assert my_friend_id in recv_json['following']

        # check if the fopllowers record is in my friend's account
        self.log_friend_in()
        self.login()
        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        assert my_user_id in recv_json['followers']


    def test_unfollow_friend(self):
        self.test_follow_friend()

        self.log_me_in()

        recv = self.app.put(apiBase+'/unfollow/'+my_friend_id)
        assert recv.status_code == 200

        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        assert my_friend_id not in recv_json['following']

        self.log_friend_in()
        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        assert my_user_id not in recv_json['followers']


    def test_not_follow_myself(self):
        self.log_me_in()

        recv = self.app.put(apiBase+'/follow/'+my_user_id)
        assert recv.status_code == 400

        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        assert my_user_id not in recv_json['following']
        assert my_user_id not in recv_json['following']


    def test_like_tweet(self):
        self.log_me_in()
        post_json = self.test_api_post_tweet()
        tweet_id = post_json['tweet_id']

        recv = self.app.put(apiBase+'/tweets/'+tweet_id+'/like')
        recv_json = json.loads(recv.data)
        assert recv.status_code == 200
        assert recv_json['result'] == 'success'
        assert recv_json['tweet_id'] == tweet_id
        assert my_user_id in recv_json['likes']


        self.log_friend_in()
        recv = self.app.put(apiBase+'/tweets/'+tweet_id+'/like')
        recv_json = json.loads(recv.data)
        assert recv.status_code == 200
        assert recv_json['result'] == 'success'
        assert recv_json['tweet_id'] == tweet_id
        assert my_friend_id in recv_json['likes']
        assert my_user_id in recv_json['likes']

        return tweet_id


    def test_unlike_tweet(self):
        tweet_id = self.test_like_tweet()

        self.log_me_in()
        recv = self.app.put(apiBase+'/tweets/'+tweet_id+'/unlike')
        recv_json = json.loads(recv.data)
        assert recv.status_code == 200
        assert recv_json['result'] == 'success'
        assert recv_json['tweet_id'] == tweet_id
        assert my_user_id not in recv_json['likes']
        assert my_friend_id in recv_json['likes']

        self.log_friend_in()
        recv = self.app.put(apiBase+'/tweets/'+tweet_id+'/unlike')
        recv_json = json.loads(recv.data)
        assert recv.status_code == 200
        assert recv_json['result'] == 'success'
        assert recv_json['tweet_id'] == tweet_id
        assert my_user_id not in recv_json['likes']
        assert my_friend_id not in recv_json['likes']
        assert recv_json['likes'] == []


    def test_logout(self):
        self.log_me_in()

        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        # self.print_json(recv_json)
        assert recv.status_code == 200
        assert recv_json['id'] == my_user_id

        recv = self.app.put(apiBase+'/user/logout')
        recv_json = json.loads(recv.data)
        # self.print_json(recv_json)
        assert recv.status_code == 200
        assert recv_json['message'] == 'success'

        recv = self.app.get(apiBase+'/user/profile')
        recv_json = json.loads(recv.data)
        # self.print_json(recv_json)
        assert recv.status_code == 401
        assert recv_json['message'] == 'not authorized'



    # Exception testing

    def test_exception_api_get_tweets_from_user(self):
        self.log_me_in()
        recv = self.app.get(apiBase+'/user/'+my_user_id+'/tweets?limit=kelvin')
        recv_json = json.loads(recv.data)
        # self.print_json(recv_json)

        assert recv.status_code == 400
        assert recv_json['message'] == 'invalid request'

    def test_exception_api_get_my_news_feed(self):
        self.log_me_in()
        recv = self.app.get(apiBase+'/user/news_feed?limit=kelvin')
        recv_json = json.loads(recv.data)

        assert recv.status_code == 400
        assert recv_json['message'] == 'invalid request'





    # HELPER FUNCTION FOR TESTING

    @classmethod
    def log_me_in(self):
        self.setup_test_env(my_user_id, my_profile)
        self.login()

    @classmethod
    def login(self):
        oAuth2.get_credentials = Mock({ })
        return self.app.get('/oAuth2Callback?code=123456')

    def log_friend_in(self):
        self.setup_test_env(my_friend_id, my_friend_profile)
        self.login()

    def print_json(self, j):
        print json.dumps(j, indent=2, sort_keys=True)


if __name__ == '__main__':
    unittest.main()
