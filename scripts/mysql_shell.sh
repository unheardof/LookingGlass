#!/bin/bash

docker exec -it $(docker ps | grep mariadb:10-focal | awk '{ print $1 }') mysql -u root -p
