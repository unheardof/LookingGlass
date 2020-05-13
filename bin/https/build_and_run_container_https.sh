#!/bin/bash

# Based on https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-application-using-docker-on-ubuntu-18-04
app="docker.looking_glass"
docker build -t ${app} .

#
# Bind port 443 on the host machine to port 443 on the container
#
# If container already exists, use the following command instead:
#
#     docker start docker.looking_glass
#
docker run -d -p 443:443 --name=${app} -v $PWD:/app ${app}
