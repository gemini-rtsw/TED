# TED Set up Instructions

1. Modify .env file to match configuration of your host
    1. DATA_PATH: Will store data from Elasticsearch and Logstash
    2. LOGS_PATH: Must contain ASCII logs files to be ingested by Logstash
    3. If it’s necessary adjust user, uid, group and gid 
2. Create folder executing ./scripts/createFolders.sh from TED’s folder
3. Execute ./scripts/prepareDocker.sh to build necessary images and network
4. Execute “docker compose up kibana” to start containers of kibana and elasticsearch (kibana depends of elasticsearch in the docker compose file)
5. Execute ./script/applyNanosES.sh to save timestamps with nanoseconds 
6. Set up logstash executing “docker compose up logstash”