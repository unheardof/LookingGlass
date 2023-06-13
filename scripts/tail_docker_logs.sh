#!/bin/bash

# To exclude the continuous GET requests from the UI, run:
# tail_docker_logs.sh 2>&1 | grep -v GET
docker logs -f $(docker ps | grep lookingglass-backend | awk '{ print $1 }')
