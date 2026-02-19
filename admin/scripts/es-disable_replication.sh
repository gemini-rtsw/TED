#!/bin/sh
curl -XPUT -H "Content-Type: application/json" "http://${HOST2_IP}:${ES1_HTTP_PORT}/_settings" -d '{
    "index": {
        "number_of_replicas": 0
    }
}'
