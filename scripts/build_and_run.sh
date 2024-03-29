#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -f "$SCRIPT_DIR/../db/password.txt" ]; then
    echo -n "Enter desired DB password (do not use @): "
    read -s db_password
    mkdir "$SCRIPT_DIR/../db"
    echo "$db_password" > "$SCRIPT_DIR/../db/password.txt"
fi

if [[ ! -f "$SCRIPT_DIR/../proxy/domain.cert" || ! -f "$SCRIPT_DIR/../proxy/domain.key" ]]; then
    cd "$SCRIPT_DIR/../proxy" && "$SCRIPT_DIR"/generate_certs.sh
fi

cd "$SCRIPT_DIR/.." && docker compose up -d

