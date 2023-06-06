#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_STAGING_DIR="/tmp/looking_glass_staging"
STAGING_DIR="$BASE_STAGING_DIR/looking_glass"

mkdir -p "$STAGING_DIR"
pushd "$STAGING_DIR" > /dev/null

cp "$SCRIPT_DIR/../prod_compose.yaml" "$STAGING_DIR/compose.yaml"
cp "$SCRIPT_DIR/../db/password.txt" "$STAGING_DIR/db_password.txt"
"$SCRIPT_DIR"/save_images.sh

tar -cvzf "$BASE_STAGING_DIR/images.tar.gz" -C "$BASE_STAGING_DIR" "looking_glass" > /dev/null

echo "#!/bin/bash" > "$BASE_STAGING_DIR/looking_glass.app"
echo "cat looking_glass.app | tr -d '\n' | sed 's/__END_OF_SCRIPT__/\n/g' | tail -n 1 | base64 -d > images.tar.gz" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "tar -xvzf images.tar.gz" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "cd looking_glass" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "for i in \$(ls); do docker load < \$i; done" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "docker compose up -d --no-build" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "cd .." >> "$BASE_STAGING_DIR/looking_glass.app"
echo "rm images.tar.gz" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "exit" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "__END_OF_SCRIPT__" >> "$BASE_STAGING_DIR/looking_glass.app"
cat "$BASE_STAGING_DIR/images.tar.gz" | base64 >> "$BASE_STAGING_DIR/looking_glass.app"

chmod +x "$BASE_STAGING_DIR/looking_glass.app"

popd > /dev/null

cp "$BASE_STAGING_DIR/looking_glass.app" .
rm -rf "$BASE_STAGING_DIR"
