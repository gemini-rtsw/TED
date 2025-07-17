
#!/bin/bash

# Load environment variables
source ./../.env

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
    "${DATA_PATH}/ls-core"
    "${DATA_PATH}/ls-core/db"
    "${DATA_PATH}/ls-core/db/sincedb"
    "${DATA_PATH}/ls-read"
    "${DATA_PATH}/ls-read/db"
    "${DATA_PATH}/ls-read/db/sincedb"
    "${DATA_PATH}/ls-read/db/completed"
    "${DATA_PATH}/archappl/db"
    "${DATA_PATH}/archappl/logs"
    "${DATA_PATH}/archappl/lts"
    "${DATA_PATH}/archappl/sts"
)

# Iterate over each directory and check/create
for dir in "${directories[@]}"; do
    create_directory_if_not_exists "$dir"
done
