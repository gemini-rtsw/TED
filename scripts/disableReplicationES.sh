#!/bin/sh
source ./.env

curl -XPUT -H "Content-Type: application/json" "http://${HOST01_PORT}:${ES01_PORT}/_settings" -d '{
    "index": {
        "number_of_replicas": 0
    }
}'
