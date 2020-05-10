#!/bin/bash
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Based on https://www.digitalocean.com/community/tutorials/how-to-build-and-deploy-a-flask-application-using-docker-on-ubuntu-18-04
app="docker.looking_glass"
docker build -t ${app} .

# Bind port 80 on the host machine to port 80 on the container
#
# If container already exists, use the following command instead:
# > sudo docker start docker.looking_glass
docker run -d -p 80:80 \
  --name=${app} \
  -v $PWD:/app ${app}
