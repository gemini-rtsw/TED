#!/bin/bash
# Lista de nombres de archivos únicos
files=(
  "cicada_cleanup"
  "cicada_data_ctl"
  "cicada_data_svc"
  "cicada_displayer"
  "cicada_gui"
  "cicada_giapi"
  "cicada_inst_ctl"
  "cicada_master"
  "cicada_messages"
  "cicada_request_svc"
  "cicada_root"
  "cicada_slave"
  "cicada_site_svc"
  "cicada_status"
  "cicada_status_svc"
  "cicada_watchdog"
  "cicada_rpc"
  "ghost_cml"
  "GhostCANSimulator"
  "giapi"
  "nrc_enclosure"
  "nrc_spectrograph"
)
for file in "${files[@]}"; do
    cp cicada_archiver.cfg ${file}.cfg
    sed -i "s/cicada_archiver/${file}/g" ${file}.cfg
done
