#### TO RUN IN DOCKER


### run fake s3 in a docker container

docker run --name my_s3 -p 4569:4569 -d lphoward/fake-s3

# https://hub.docker.com/r/lphoward/fake-s3/





### build and run redis
from this website
https://rominirani.com/docker-tutorial-series-part-8-linking-containers-69a4e5bf50fb#.blopip6v1
docker pull redis
docker run -d --name my_redis -p 6379:6379 redis





### Trying this 
docker build -t tweetsme ./app
docker run -d --restart=always -p 80:80 -t tweetsme 
docker run --link my_s3:s3.amazonaws.com --link my_redis:redis --restart=always --name tm -p 80:80 -t tweetsme
(^ this works)
(NOTE: -d is damonizing the docker container)



### RUN locally (without docker)
sudo fakes3 -r /mnt/fakes3_root -p 4569
redis-server



### TODO when deploy
* set up OAuth consent screen and logo
* change rediectURI for OAuth on google credentials






