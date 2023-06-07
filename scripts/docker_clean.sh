#!/bin/bash

docker container prune -f

docker image rm -f lookingglass-backend
docker image rm -f lookingglass-proxy

