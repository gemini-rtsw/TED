if ! docker network ls | grep -q elkg; then
    echo "Creating Docker network: elkg"
    docker network create elkg
else
    echo "Docker network already exists: elkg"
fi

# Build and launch Docker containers
docker compose build --no-cache elasticsearch gearservice grafana logstash_01
