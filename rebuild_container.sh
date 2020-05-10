#!/bin/bash

app="docker.looking_glass"
docker build -t ${app} .
sudo docker stop docker.looking_glass
sudo docker start docker.looking_glass
