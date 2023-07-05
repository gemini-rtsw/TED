# TED
1. Create data folder

2. This folder will contain Elasticsearch indexes and Logstash auxiliary files 

3. Check logs input folder.
    Check that you have access to subsystem’s logs

4. Create elkg network on docker
   -> docker network create elkg

5. Modify .env file
    You must specify the following variables:
    HOST_IP: Host machine IP, you can use the ifconfig command to get this information.
    U_ID: The id of your user, use the id command to get this information.
    G_ID: The id of the group owner of the folders [data] and [TED].
    DATA_PATH: Path where elasticsearch indexes and logstash auxiliary files will be stored (folder created in step 1)
    LOGS_PATH: Path where the input logs are stored (subsystems logs, step 2)
    LS_TIMEZONE: Set the timezone for logstash to ingest information

6. Execute createFolders script
    From TED path execute ./scripts/createFolders.sh 
    This will create needed folders to Elasticsearch and Logstash

7. Check permissions of folders, it is important to give permissions to write and execute to the group specified in the .env (gemini(2000))
    - chmod -R 770 [data folder]
    - chmod -R 770 [TED folder]
    
8. Change group ownership of the folders to "gemini(2000)"
    It is necessary that the folder is owned by the group which its G_ID is defined on step 3 (in this case “gemini(2000)”)
    - chgrp -R gemini [TED_folder]
    - chgrp -R gemini [data_folder]

9. Execute docker compose up elasticsearch
    After a minute, elasticsearch will be up, and you will be able to see the es01 info as response on [HOST_IP]:[ES01_PORT] (9200 by default)

10. Execute applyNanoES script
    To configure nanoseconds resolution on Elasticsearch, from TED path execute ./scripts/applyNanoES.sh 

11. Execute disableReplicationES.sh
    You need to specify 0 replicas, otherwise, the status of the indexes will be yellow. From TED path execute ./scripts/disableReplicationES.sh 

12. Execute docker compose up kibana
    This will set up kibana and automatically connect it with elasticsearch
    After a couple of minutes, you will be able to enter Kibana going to [HOST_IP]:[KI01_PORT] (5601 by default)

13. Execute docker compose up logstash_01
    If logstash is running okay you will be able to see the incoming data streams on Kibana. Be sure that pipelines are running and that it is well configured on pipelines.yml file.

14. Create a new Data View with Name=“Logs” and 
    Index Pattern=“ logs-* ”, the pattern will indicate which indexes will be available in that Data View (for example, logs-cpo* will take logs-cpo-dhs, logs-cpo-gacq, and so on). This is for Kibana only.

15. On the TED folder path, 
    execute ./scripts/cronJobLS.sh script: Logstash (ls01) needs 
    to restart after file rotation, otherwise it gets stuck in an Unknown Error

16. On the TED folder path, execute docker compose up geaservice to 
    set up geaservice middleware. Check if the GEA URL on geaservice.py is correct.
    gea = xmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')
    You need to restart the service to apply changes on geaservice.py
    If you request [HOST_IP]:[GS01_PORT]/archives and receive a json with the archivers info, then geaservice is running correctly.

17. Set up Grafana executing docker compose up grafana 
    After a minute, you’ll be able to enter Grafana on [HOST_IP]:[GR01_PORT] 

18. Change Grafana datasources services ip's to the HOST_IP

19. When you’re ready, execute docker compose up logstash_02 to 
    load historical data. See Load historical

