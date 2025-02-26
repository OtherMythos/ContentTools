#!/bin/bash -x

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if [ -z "$1" ]; then
  echo "Please provide an input directory"
  exit 1
fi

if [ -z "$2" ]; then
  echo "Please provide an input thumbnail"
  exit 1
fi

CONTENT_DIR="$1/Channel content - YouTube Studio_files"
TARGET_FILE="$CONTENT_DIR/mqdefault(4)"
cd "$CONTENT_DIR"
rm *.js
rm "$TARGET_FILE.jpg"
rm "$TARGET_FILE.webp"

cp "$2" "$TARGET_FILE.webp"
cp "$2" "$TARGET_FILE.jpg"