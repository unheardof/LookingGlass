#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ ! -f "$SCRIPT_DIR/../db/password.txt" ]; then
    read -p "Enter desired DB password: " db_password
    echo "$db_password" > "$SCRIPT_DIR/../db/password.txt"
fi

cd "$SCRIPT_DIR/.." && docker compose up

