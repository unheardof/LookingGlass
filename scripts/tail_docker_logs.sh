#!/bin/bash

docker logs -f $(docker ps | grep lookingglass-backend | awk '{ print $1 }')
