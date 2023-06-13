#!/bin/bash

docker attach $(docker ps | grep lookingglass-backend | awk '{ print $1 }')
