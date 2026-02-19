#!/bin/bash

# Source and destination paths
source="/gemsoft/var/log/flam-pre"
destination="/gemsoft/var/log/flam-post"

# Ensure the destination directory exists
mkdir -p "$destination"

# Compare and copy new lines
for file in "$source"/*; do
    # Extract just the filename
    filename=$(basename "$file")
    dest_file="$destination/$filename"

    # If the file already exists in the destination, compare it
    if [ -e "$dest_file" ]; then
        # Copy only the new lines that are not in the destination
        diff "$dest_file" "$file" | grep '^>' | sed 's/^> //g' >> "$dest_file"
    else
        # If it doesn't exist, simply copy the file
        cp "$file" "$dest_file"
    fi
done

# Remove files from destination that do not exist in source
for file in "$destination"/*; do
    filename=$(basename "$file")
    source_file="$source/$filename"

    if [ ! -e "$source_file" ]; then
        rm -f "$destination/$filename"
    fi
done

