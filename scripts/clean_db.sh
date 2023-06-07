#!/bin/bash

docker image rm -f mariadb:10-focal

for volume in $(docker volume ls | grep looking | grep glass | grep db-data | awk '{ print $2 }'); do
    docker volume rm "$volume"
done
