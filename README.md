# TED Setup Instructions

1. **Initial verification**
   - **Check data folder**: Identify the data folder or create a new folder.
   - **Check Logs Input Folder**: Ensure access to subsystem’s logs.
   - **Access TED Folder**: Navigate to the TED folder for the follow steps.


2. **Configuration**
   - **Modify .env File**: Adjust to match your host settings.
     - `DATA_PATH`: Directory to store data from Elasticsearch and Logstash.
     - `LOGS_PATH`: Must contain ASCII log files for Logstash ingestion.
     - `LS_TIMEZONE`: Set the timezone for Logstash data ingestion.
     - Adjust `USER`, `U_ID`, `GROUP`, and `G_ID` if necessary.

3. **Folder Creation**
   - **Execute `./scripts/createFolders.sh`**: Creates necessary folders for Elasticsearch and Logstash.

4. **Docker Preparation**
   - **Run `./scripts/prepareDocker.sh`**: Builds necessary Docker images and network.

5. **Kibana and Elasticsearch**
   - **Execute `docker compose up kibana`**:
     - Automatically configures and connects Kibana and Elasticsearch.
     - Access Kibana at `[HOST_IP]:[KI01_PORT]` (default 5601) after a few minutes.

6. **Elasticsearch Nanoseconds Resolution**
   - **Run `./scripts/applyNanoES.sh`** from the TED path:
     - Configures nanoseconds resolution on Elasticsearch.

7. **Logstash**
   - **Execute `docker compose up logstash`**:
     - Check for incoming data streams on Kibana.
     - Ensure pipelines are configured correctly in `pipelines.yml`.

8. **Kibana Data View**
   - **Create a New Data View in Kibana**:
     - Name: “Logs”
     - Index Pattern: “logs-*”
     - This will indicate which indexes are available in the Data View.

9. **Elasticsearch Replication**
   - **Run `./scripts/disableReplicationES.sh`**:
     - Specify 0 replicas to prevent index status from being yellow.

10. **Logstash File Rotation**
    - **Execute `./scripts/cronJobLS.sh`**:
      - Necessary for Logstash (`ls01`) to restart after file rotation.

11. **GEA Service Middleware**
    - **Run `docker compose up geaservice`** in the TED folder path:
      - Check and adjust the GEA URL in `geaservice.py`.
      - Restart the service after changes.
      - Verify by requesting `[HOST_IP]:[GS01_PORT]/archives`.

12. **Grafana**
    - **Execute `docker compose up grafana`**:
      - Access Grafana at `[HOST_IP]:[GR01_PORT]` after a minute.
