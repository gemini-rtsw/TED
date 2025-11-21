#!/bin/bash
docker exec -i grafana sqlite3 /var/lib/grafana/grafana.db .dump > ../grafana.sql