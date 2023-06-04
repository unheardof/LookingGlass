#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/../looking_glass"

# TODO: Update to use HTTPS
FLASK_APP=application.py flask run --host=0.0.0.0
