#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR"/..
docker compose down
"$SCRIPT_DIR"/docker_clean.sh
"$SCRIPT_DIR"/build_and_run.sh
