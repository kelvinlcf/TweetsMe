import logging


S3_BUCKET_NAME = 'hdems-test-01-kelvin'
LOG_FILE = 'logger.log'
LOG_LEVEL = logging.INFO

# web app credential
CLIENT_SECRET_FILE = 'client_secret_556143299795-akv8b61sea9sebcgq3co68q35tu8hrmo.apps.googleusercontent.com.json'

HOSTED_DOMAIN_RESTRICTION = False
ALLOWED_HOSTED_DOMAIN = 'g.hde.co.jp'
MAX_SEARCH_RESULT = 10
MAX_MESSAGE_LENGTH = 140

ALLOWED_CONTENT_TYPE_FOR_IMAGES = ["image/jpeg","image/png"]

API_VERSION = "v1.0"
REDIS_HOST = 'redis'

# REDIS_HOST = 'localhost'
REDIS_PORT = '6379'

# change to localhost to run test locally
# S3_ENDPOINT_HOST = 'localhost'
S3_ENDPOINT_HOST = 's3.amazonaws.com'

MOODS_JSON_FILE = 'static/data/moods.json'