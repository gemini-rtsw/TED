#!/bin/bash

init() {
  echo $COMPOSE_PATH
  source $COMPOSE_PATH/.env
  echo $SCRIPTS_PATH
  source $SCRIPTS_PATH/$site/create_folders.sh
  # configure_elasticsearch
}
configure_elasticsearch(){
  read hostname lvx < <(get_hostname "2")
  source $COMPOSE_PATH/.env
  echo "Waiting for $HOST2_IP:$ES1_HTTP_PORT..."
  while ! curl -s --connect-timeout 2 "http://${HOST2_IP}:${ES1_HTTP_PORT}" >/dev/null; do
    sleep 2
  done
  echo "Elasticsearch API is ready, executing scripts..."
  echo "Applying nanoseconds timestamps"
  source $SCRIPTS_PATH/es-apply_nanos.sh
  echo "Changing retrieval limits"
  source $SCRIPTS_PATH/es-change_hits_limit.sh
  echo
  echo "Disabling replication"
  source $SCRIPTS_PATH/es-disable_replication.sh
  echo
}
get_ps() {
  for i in {1..3}; do
    read hostname lvx < <(get_hostname "$i")
    echo "$hostname"
    ssh -n $hostname "docker ps"
  done 
}
get_stats() {
  for i in {1..3}; do
    read hostname lvx < <(get_hostname "$i")
    echo "$hostname"
    ssh -n $hostname "docker stats --no-stream"
  done 
}
get_hostname() {
  local node_num="$1"
  # If no argument was provided → ask interactively
  if [[ -z "$node_num" ]]; then
    while true; do
      read -p "Enter TED node number (1-3): " node_num
      case "$node_num" in
        1|2|3) break ;;
        *) echo "Invalid input. Enter 1, 2, or 3." ;;
      esac
    done
  fi
  case "$node_num" in
    1|2|3) ;;
    *) echo "Invalid node number: $node_num" >&2; return 1 ;;
  esac

  local hostname="${host_prefix}ted${host_suffix}-lv${node_num}"
  echo "$hostname lv${node_num}"
}
remove_all_containers() {
  read hostname lvx < <(get_hostname)
  echo "Executing docker compose down on $hostname"
  ssh -n $hostname "docker compose -f ${COMPOSE_PATH}/${lvx}.yml down"
  echo "Done"
}
compose_all_containers() {
  read hostname lvx < <(get_hostname)
  echo "Executing docker compose up on $hostname"
  ssh -n $hostname "docker compose -f ${COMPOSE_PATH}/${lvx}.yml up -d"
  echo "Done"
}

site=$1
env=$2
[[ "$1" =~ ^(CP|MK)$ ]] || { echo "First arg must be CP or MK"; exit 1; }
[[ "$2" =~ ^(dev|prod)$ ]] || { echo "Second arg must be dev or prod"; exit 1; }
if [ "$site" == "CP" ]; then host_prefix="cpo"; else host_prefix="mko" ;fi
if [ "$env" == "dev" ]; then host_suffix="dev"; else host_suffix="" ;fi

THIS_PATH="$(realpath "$0")"
ADMIN_PATH=$(dirname "$THIS_PATH")
COMPOSE_PATH="$ADMIN_PATH/$site"
SCRIPTS_PATH="${ADMIN_PATH}/scripts"

while true; do
  echo "=============================="
  echo "   Docker Setup Menu"
  echo "=============================="
  echo "1) Get 'docker ps' for all containers"
  echo "2) Execute 'docker stats' for a specific host"
  echo "3) Execute 'docker compose up' for a specific host"
  echo "4) Execute 'docker compose down' for a specific host"  
  echo "5) Initialize environment"
  echo "6) Execute Elasticsearch scripts"
  echo "9) Exit"
  echo
  read -p "Choose an option: " option

  case $option in
    1)
      get_ps
      ;;
    2)
      get_stats
      ;;
    3)
      compose_all_containers
      ;;
    4)
      remove_all_containers
      ;;
    5)
      init
      ;;
    6)
      configure_elasticsearch
      ;;  
    9)
      echo "Goodbye!"
      exit 0
      ;;
    *)
      echo "Invalid option"
      sleep 1
      ;;
  esac
done