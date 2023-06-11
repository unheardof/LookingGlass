#!/bin/bash

sudo rm /app/domain.key
sudo rm /app/domain.crt
openssl req -newkey rsa:2048 -nodes -keyout domain.key -x509 -days 365 -out domain.crt -subj "/C=US/ST=New York/L=Brooklyn/O=Example Company/CN=examplecompany.com"
#sudo chmod 640 /app/domain.key

