#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

"$SCRIPT_DIR"/install_docker.sh

cd "$SCRIPT_DIR/.."
python3 -m venv ./venv
source venv/bin/activate
pip install -r backend/looking_glass/requirements.txt

sudo yum install -y mariadb105
