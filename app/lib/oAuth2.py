import flask

import properties
from oauth2client import client
import os
import logger
import httplib2
import apiclient


def create_flow():
    flow = client.flow_from_clientsecrets(
        properties.CLIENT_SECRET_FILE,
        scope='openid profile email',
        redirect_uri=flask.url_for('oauth2_callback',_external=True))
    return flow

# Step 1
def get_authorize_url():
    flow = create_flow()
    return flow.step1_get_authorize_url()

# Step 2
def exchange_credentials(auth_code):
    flow = create_flow()
    credentials = flow.step2_exchange(auth_code)
    # store token and credentials to session
    flask.session['credentials'] = credentials.to_json()
    # pull the Credentials object from session
    credentials = get_credentials()
    # getting name and email from google api
    http_auth = credentials.authorize(httplib2.Http()) # http auth object
    user_info_json = apiclient.discovery.build('oauth2','v2', http=http_auth).userinfo().get().execute()
    return user_info_json


def get_credentials():
    if 'credentials' in flask.session:
        return client.OAuth2Credentials.from_json(flask.session['credentials'])
    else:
        return None
