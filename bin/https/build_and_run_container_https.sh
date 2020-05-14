#!/bin/bash

# Based on https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-application-using-docker-on-ubuntu-18-04

APP="docker.looking_glass"

# Navigate to the root project directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ../..

docker build --build-arg NGINX_CONF_FILE='./https_nginx.conf' -t ${APP} .

#
# Bind port 443 on the host machine to port 443 on the container
#
# If container already exists, use the following command instead:
#
#     docker start docker.looking_glass
#
docker run -d -p 443:443 --name=${APP} -v $PWD:/app ${APP}
