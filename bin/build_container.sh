#!/bin/bash

# Based on https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-application-using-docker-on-ubuntu-18-04

APP="docker.looking_glass"

# Reference: https://stackoverflow.com/questions/3822621/how-to-exit-if-a-command-failed/3822709
bin/run_tests.sh || { echo 'Tests failed; aborting build'; exit 1; }

if docker container ls | awk '{if(NR>1)print $2}' | grep $APP; then
    echo 'Stopping and removing existing container...'
    docker stop docker.looking_glass
    docker rm docker.looking_glass
fi

if docker images | awk '{if(NR>1)print $1}' | grep $APP; then
    echo 'Removing existing container image...'
    docker rmi docker.looking_glass
fi

docker build --build-arg NGINX_CONF_FILE='./http_nginx.conf' -t ${APP} .
