#!/bin/bash

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
    "${DATA_PATH}elasticsearch-1"
    "${DATA_PATH}elasticsearch-2"
    "${DATA_PATH}ls-core/db/sincedb"
    "${DATA_PATH}ls-guiders/db/sincedb"
    "${DATA_PATH}ls-opstools/db/sincedb"
    "${DATA_PATH}ls-gmos/db/sincedb"
    "${DATA_PATH}ls-altair/db/sincedb"
    "${DATA_PATH}ls-gnirs/db/sincedb"
    "${DATA_PATH}ls-instruments/db/sincedb"
    "${DATA_PATH}archappl/db"
    "${DATA_PATH}archappl/logs"
    "${DATA_PATH}archappl/lts"
    "${DATA_PATH}archappl/mts"
    "${DATA_PATH}archappl/sts"
)

# Iterate over each directory and check/create
for dir in "${directories[@]}"; do
    create_directory_if_not_exists "$dir"
done
