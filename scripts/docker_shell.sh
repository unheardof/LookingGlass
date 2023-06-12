#!/bin/bash

docker exec -it $(docker ps | grep lookingglass-backend | awk '{ print $1 }') /bin/sh
