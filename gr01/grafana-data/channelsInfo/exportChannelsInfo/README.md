TED Channels names

GEA config: Data with GEA format 
/ted-channels-names/config/gea-config

TED config: Data with TED format
/ted-channels-names/config/ted-config

Instructions:
1. Copy GEA config folders in ./config/gea-config
2. Execute "translate-cofig.py" to convert the configuration in TED format as JSON
3. If you want, edit the JSON configuration
4. Execute "create-db.py" to insert the configuration in the "ted-channels.db" file

To use db in Grafana:
1. Copy the "ted-channels.db" in Grafana
2. Configure a SQLite data source in Grafana