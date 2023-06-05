#!/bin/bash

docker container prune -f
docker image rm -f lg-mysql-backend
docker image rm -f lg-mysql-proxy

