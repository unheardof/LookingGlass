#!/bin/bash

APP="docker.looking_glass"
docker stop ${APP}
docker build -t ${APP} .
docker start ${APP}
