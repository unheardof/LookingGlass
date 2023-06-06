#!/bin/bash

docker save lookingglass-backend:latest > lookingglass-backend.tar
docker save lookingglass-proxy:latest > lookingglass-proxy.tar
docker save mariadb:10-focal > mariadb.tar
