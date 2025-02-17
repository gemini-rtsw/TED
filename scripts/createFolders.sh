
#!/bin/bash

# Load environment variables
source ./.env

# Function to check and create directories if they do not exist
create_directory_if_not_exists() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    else
        echo "Directory already exists: $dir"
    fi
}

# List of directories to check/create
directories=(
    "${DATA_PATH}/es01"
    "${DATA_PATH}/ls01"
    "${DATA_PATH}/ls01/db"
    "${DATA_PATH}/ls01/db/sincedb"
    "${DATA_PATH}/ls02"
    "${DATA_PATH}/ls02/db"
    "${DATA_PATH}/ls02/db/sincedb"
    "${DATA_PATH}/ls02/db/completed"
    "${DATA_PATH}/ls02/db/completed"
    "${DATA_PATH}/ls03/db"
    "${DATA_PATH}/ls03/db/sincedb"
    "./es01/logs"
)

# Iterate over each directory and check/create
for dir in "${directories[@]}"; do
    create_directory_if_not_exists "$dir"
done
