
import properties
from uuid import uuid4
import json
import re

def build_api_path(custom_path):
    # api base path
    return "/api/"+properties.API_VERSION+custom_path


def gen_unique_id():
    return str(uuid4())

def dict_to_json(dict):
    return json.dumps(dict, separators=(',',':'), indent=2)

def get_redis_list_name(user_id, key):
    return user_id+"."+key

def is_redis_main_list_key(key):
    return re.match('^[^.]+$',key)


def get_http_url(url):
    return re.sub('^https', 'http', url)

def hosted_domain_verification(user_info):
	return (not properties.HOSTED_DOMAIN_RESTRICTION or
	    ('hd' in user_info and user_info['hd'] == properties.ALLOWED_HOSTED_DOMAIN))

def extract_timestamp(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return float(json['timestamp'])
    except KeyError:
        return 0

def load_json_file(file_path):
    data = {}
    with open(file_path) as data_file:
        data = json.load(data_file)
    return data

def validate_color(color):
    if color == '':
        return True
    availableMoods = load_json_file(properties.MOODS_JSON_FILE)
    for obj in availableMoods:
        if obj['color'] == color:
            return True
    return False