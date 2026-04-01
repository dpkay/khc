#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "Building..."
npm run build

echo "Deploying to HAOS..."
scp -r dist/* root@192.168.1.20:/config/www/

echo "Done: http://192.168.1.20:8123/local/index.html"
