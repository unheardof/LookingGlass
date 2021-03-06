#!/bin/bash

# Navigate to the root project directory
cd $(dirname "${BASH_SOURCE[0]}")
cd ../..

source bin/build_container.sh

#
# Bind port 80 on the host machine to port 80 on the container
#
# If container already exists, use the following command instead:
#
#     docker start docker.looking_glass
#
docker run -d -p 80:80 --name=${APP} -v $PWD:/app ${APP}
