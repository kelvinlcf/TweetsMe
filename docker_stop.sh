#!/bin/sh

docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)



# cmd to run fake-s3
# docker run --name my_s3 -p 4569:4569 -d lphoward/fake-s3

# cmd to stop fake-s3
# docker pull lphoward/fake-s3

# https://hub.docker.com/r/lphoward/fake-s3/