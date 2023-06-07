#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_STAGING_DIR="/tmp/looking_glass_staging"
STAGING_DIR="$BASE_STAGING_DIR/looking_glass"

read -p "This will stop the running cluster and clear out the local database. Continue (y|n)? " proceed

if [ "$proceed" != "y" ]; then
    exit
fi

pushd "$SCRIPT_DIR/.." > /dev/null

"$SCRIPT_DIR"/stop_cluster.sh
"$SCRIPT_DIR"/docker_clean.sh
"$SCRIPT_DIR"/clean_db.sh

docker compose up -d

mkdir -p "$STAGING_DIR"
cd "$STAGING_DIR" 

# Copy scripts for stopping and starting the cluster (with up --no-build)
cp "$SCRIPT_DIR/../prod_compose.yaml" "$STAGING_DIR/compose.yaml"
cp "$SCRIPT_DIR/../docs/bundled_app_readme.md" "$STAGING_DIR/README.md"
cat "$SCRIPT_DIR/start_cluster.sh" | sed 's/SCRIPT_DIR\/\.\./SCRIPT_DIR/' > "$STAGING_DIR/start_cluster.sh"
cat "$SCRIPT_DIR/stop_cluster.sh" | sed 's/SCRIPT_DIR\/\.\./SCRIPT_DIR/' > "$STAGING_DIR/stop_cluster.sh"

"$SCRIPT_DIR"/save_images.sh

tar -cvzf "$BASE_STAGING_DIR/images.tar.gz" -C "$BASE_STAGING_DIR" "looking_glass" > /dev/null

echo "#!/bin/bash" > "$BASE_STAGING_DIR/looking_glass.app"
echo "echo -n 'Enter desired DB password (do not use @): '" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "read -s db_password" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "cat looking_glass.app | tr -d '\n' | sed 's/__END_OF_SCRIPT__/\n/g' | tail -n 1 | base64 -d > images.tar.gz" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "tar -xvzf images.tar.gz" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "cd looking_glass" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "echo \"\$db_password\" > db_password.txt" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "chmod +x start_cluster.sh" >> "$BASE_STAGING_DIR/looking_glass.app"
echo "chmod +x stop_cluster.sh" >> "$BASE_STAGING_DIR/looking_glass.app"
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
