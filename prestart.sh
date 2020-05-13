#!/bin/bash

openssl req -newkey rsa:2048 -nodes -keyout /tmp/domain.key -x509 -days 365 -out /tmp/domain.crt -subj "/C=US/ST=New York/L=Brooklyn/O=Example Company/CN=examplecompany.com"
