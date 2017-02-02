A twitter clone project
======



## Features of TweetsMe


### Basic features
* google openID login
* login restriction by domain in ```hd``` field of the google openID credentials
* create and delete tweet post
* like and unlike tweet post
* follow and unfollow user
* news feed page for all the recent posts
* multi language support
* emoji support
* user search
* https encryption with **Let's encrypt** certificate
* single button login in home page (clean design)

### Advance features
* customizable font for tweet post
* user specified mood
* infinite scroll when viewing tweets


## Running the server

### Run with docker compose
* ``` docker-compose up --build ```

### Run individually with docker
* ```docker build -t tweetsme ./app```
* ```docker run -d --restart=always -p 80:80 -t tweetsme```
* ```docker run --link my_s3:s3.amazonaws.com --link my_redis:redis --restart=always --name tm -p 80:80 -t tweetsme```

* (NOTE: -d is damonizing the docker container)



### Run locally (without docker) in virtual env
1. ```redis-server```
2. ```sudo fakes3 -r /mnt/fakes3_root -p 4569```
3. ```python app/web.py```

### Running only fake s3 in a docker container
* ```docker run --name my_s3 -p 4569:4569 -d lphoward/fake-s3```
* https://hub.docker.com/r/lphoward/fake-s3/


## When deploy to AWS
* [ ]At s3Handler, change ```boto3.client``` to ```boto3.client``` with credentials field
* [ ]At ```docker-compose```
  * [ ]Remove f```ake-s3:s3.amnaxonaws.com``` and the ```fake-s3``` service
* [ ]login restriction enable
* [ ] Mac /etc/letsencrypt have private in the front
  * should become ```/private/etc/....``` for mac
  * and ```/etc/.....``` for linux

## TODO
* [ ]my tweet to news feed page

## Tech Stack
* ```Sngular JS```
* ```Semantic-ui```
* ```Python Flask```
* ```Docker```
* ```Redis```
* ```S3```
* ```Nginx with uWSGI```
