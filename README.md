# TED
1 modify .env file
2 execute createFolders script
3 check permissions of folders, it is important to give permissions to write and execute to the group specified in the .env
    - chmod -R 770 [data_folder]
    - chmod -R 770 [grafana_data]
4 docker compose up elasticsearch
5 execute applyNanoES script
6 docker compose up kibana
7 docker compose up logstash_01
8 docker compose up logstash_02
9 execute cronJobLS script: Logstash needs to restart after file rotation, otherwise it gets stuck in an Uknown Error
10 change grafana datasources services ip's to the host IP