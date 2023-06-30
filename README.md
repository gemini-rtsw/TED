# TED
1. modify .env file
2. execute createFolders script
3. check permissions of folders, it is important to give permissions to write and execute to the group specified in the .env (gemini(2000))
    - chmod -R 770 [data folder]
    - chmod -R 770 [TED folder]
4. change group ownership of the folders to "gemini(2000)"
    - chgrp -R gemini [TED_folder]
    - chgrp -R gemini [data_folder]
5. docker compose up elasticsearch
6. execute applyNanoES script
7. docker compose up kibana
8. docker compose up logstash_01
9. docker compose up logstash_02 (HISTORICAL LOAD)
10. execute cronJobLS script: Logstash (ls01) needs to restart after file rotation, otherwise it gets stuck in an Uknown Error
11. change grafana datasources services ip's to the host IP