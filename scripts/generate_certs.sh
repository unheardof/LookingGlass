#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

openssl req -newkey rsa:4096 -nodes -keyout domain.key -x509 -signkey -sha256 -days 365 -out domain.crt -subj "/C=US/ST=New York/L=Brooklyn/O=Example Company/CN=examplecompany.com" &> /dev/null

chmod 0400 domain.key
