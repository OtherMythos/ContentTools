#!/bin/bash -x

# Define the directory to search for .mov files
DIR="/Users/edward/rec"

# Iterate over all .mov files in the directory
for file in "$DIR"/*.mov; do
  # Check if the file exists (in case there are no .mov files)
  [ -e "$file" ] || continue

  if [[ $file == *".reduced"* ]]; then
    continue
  fi

  # Define the output file name
  reduced_file="${file%.mov}.reduced.mov"

  # Skip processing if the .reduced.mov file already exists
  if [ -e "$reduced_file" ]; then
    echo "Skipping $file, reduced version already exists."
  else
    # Run ffmpeg command
    ffmpeg -i "$file" -filter:v fps=30 "$reduced_file"
    echo "Processed $file to $reduced_file"
  fi
done
