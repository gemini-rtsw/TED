#!/bin/sh
source ./.env

curl -XPUT -H "Content-Type: application/json" "http://localhost:${ES01_PORT}/_settings" -d '{
    "index": {
        "number_of_replicas": 0
    }
}'
