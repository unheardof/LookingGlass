#!/bin/bash

# Navigate to the root project directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ../..

# TODO: Build the HTTPS version of the container (with certificate generation, etc.)
source bin/build_container.sh

#
# Bind port 443 on the host machine to port 443 on the container
#
# If container already exists, use the following command instead:
#
#     docker start docker.looking_glass
#
docker run -d -p 443:443 --name=${APP} -v $PWD:/app ${APP}
