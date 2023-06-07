#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

read -p "This will stop the running cluster, clear out the local database, and clear the Docker cache. Continue (y|n)? " proceed

if [ "$proceed" != "y" ]; then
    exit
fi

"$SCRIPT_DIR"/stop_cluster.sh
"$SCRIPT_DIR"/docker_clean.sh
"$SCRIPT_DIR"/clean_db.sh

docker container prune -f
