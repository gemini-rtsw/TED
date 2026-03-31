#!/bin/python3
import os
import subprocess
import argparse
import json
import yaml
import logging
import time
import calendar
from datetime import datetime, timedelta

from pathlib import Path


# --- Logger Setup ---
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='insertData.log',
        filemode='a'
    )

# --- Retry Helper ---
def retry_cmd(command, retries=3, delay=3):
    for attempt in range(retries):
        try:
            subprocess.run(command, check=True)
            return
        except subprocess.CalledProcessError as e:
            logging.warning(f"Retry {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    logging.error(f"Command failed after {retries} retries: {' '.join(command)}")


# --- Environment Handling ---
def load_env(path="/gemsoft/opt/TED/TED/admin/CP/.env"):
    envDict = {}
    try:
        with open(path, "r") as file:
            for line in file:
                key, _, value = line.partition("=")
                envDict[key.strip()] = value.strip()
    except Exception as exc:
        logging.error(f"Error loading environment file: {exc}")
    return envDict

# --- Pipeline Configuration ---
def load_systems():
    dict_pipelines = {}
    base_dir = Path("pipeline")
    dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    for d in dirs:
        cfg_files = list(d.rglob("*.cfg"))
        dict_pipelines[d.name] = {}
        for f in cfg_files:
            dict_pipelines[d.name][f.stem] = f
    return dict_pipelines

def print_tree(data):
    for group, files in data.items():
        print(group)
        for name in files:
            print(f"  └─ {name}")

def get_pipeline_path(system_name, systems_dict):
    for group in systems_dict.values():
        if system_name in group:
            return group[system_name]
    return None

def create_pipeline_file(systems_dict, systems, outputPath="./config/pipelines.yml"):
    list_systems_args = systems.split(',')
    pipelines_ids = []
    try:
        with open(outputPath, 'w+') as file:
            for system_name in list_systems_args:
                file.write(f"- pipeline.id: cp-{system_name}-read\n")
                file.write(f"  pipeline.workers: 1\n")
                file.write(f"  path.config: /usr/share/logstash/{get_pipeline_path(system_name, systems_dict)}\n")
                file.write(f"  queue.type: persisted\n")
                file.write(f"  queue.max_bytes: 100mb\n\n")
                pipelines_ids.append(f"cp-{system_name}-read")
        return pipelines_ids
    except Exception as exc:
        logging.error(f"Error creating pipelines file: {exc}")
def get_dates_by_month(startDate, endDate):
    grouped = {}
    try:
        start = datetime.strptime(startDate, "%Y/%m/%d").date()
        end = datetime.strptime(endDate, "%Y/%m/%d").date()
    except ValueError as exc:
        logging.error(f"Date format error: {exc}")
        return []

    while start <= end:
        ymKey = (start.year, start.month)
        grouped.setdefault(ymKey, []).append(start.day)
        start += timedelta(days=1)

    return [[f"{y:04d}", f"{{{m:02d},{calendar.month_abbr[m]}}}", f"{{{','.join(f'{d:02d}' for d in days)}}}", calendar.month_abbr[m]]
            for (y, m), days in grouped.items()]

def docker_up(date, env):
    os.environ.update({
        'HOST2_IP': env.get('HOST2_IP'),
        'ES1_HTTP_PORT': env.get('ES1_HTTP_PORT', ''),
        'LS_TIMEZONE': env.get('LS_TIMEZONE', ''),
        'LOGS_PATH': env.get('LOGS_PATH', ''),
        'DATA_PATH': env.get('DATA_PATH', ''),
        'DAY': date[2],
        'MONTH': date[1],
        'YEAR': date[0],
    })
    retry_cmd(['/bin/docker', 'compose', '-f', './ls-read.yml', 'up', '-d', 'ls-read'])


def docker_down():
    retry_cmd(['/bin/docker', 'rm', '-f', 'ls-read'])

# --- Pipeline Monitoring ---
def checkPipelineCompletion(pipelineNames):
    finished = set()
    total = len(pipelineNames)
    while len(finished) < total:
        for name in pipelineNames:
            if name in finished:
                continue
            cmd = f"docker exec ls-read curl -sS 'http://localhost:9660/_node/stats/pipelines/{name}'"
            try:
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    raise Exception(result.stderr.decode())
                stats = json.loads(result.stdout.decode())
                pipelineStats = stats.get('pipelines', {}).get(name, {})
                flow = pipelineStats.get('flow', {})
                events = pipelineStats.get('events', {})

                flowCondition = True

                for m in ['output_throughput', 'filter_throughput', 'input_throughput','queue_backpressure', 'queue_persisted_growth_bytes', 'queue_persisted_growth_events']:
                    value = flow.get(m, {}).get('current', -1)
                    comparison = (value == 0.0)
                    # print(f"{m}: current={value} → {comparison}")
                    if not comparison:
                        flowCondition = False

                eventsIn = events.get('in', 0)
                eventsOut = events.get('out', 0)
                
                eventsCondition = eventsIn == eventsOut

                print(f"{name} > Events detected: {eventsIn}, Events checked: {eventsOut}")

                if flowCondition and eventsCondition:
                    finished.add(name)
                    print(f"✔ Finished: {name}")
            except Exception as e:
                logging.error(f"Error monitoring pipeline {name}: {e}")
        time.sleep(5)

def handle_docker(env, pipelines_ids, date_from, date_to):
    for dates_by_month in get_dates_by_month(date_from, date_to):
        print(f"INSERTING LOGS FOR {dates_by_month[0]} | {dates_by_month[-1]} | {dates_by_month[2]}")
        docker_up(dates_by_month, env)
        checkPipelineCompletion(pipelines_ids)
        docker_down()

# --- Main Menu ---
def main():
    setup_logger()
    systems_dict = load_systems()
    env = load_env()
    defaultEndDate = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
    parser = argparse.ArgumentParser(
        description="Pipeline configuration scanner"
    )

    subparsers = parser.add_subparsers(dest="command")
    #------------------------------------------------------------------------------
    parser_list = subparsers.add_parser(
        "list",
        help="List available systems"
    )
    #------------------------------------------------------------------------------
    parser_system = subparsers.add_parser(
        "system",
        help="Load specific system"
    )
    parser_system.add_argument(
        "systems",
        help="Subsystem name (e.g. tcs, vii, f2-wfs). Also, you can separate multiple systems using a ',' (e.g ag,f2-opc)"
    )
    parser_system.add_argument(
        "date_from",
        help="Start date (YYYY/MM/DD)"
    )
    parser_system.add_argument(
        "date_to",
        help="End date (YYYY/MM/DD)"
    )
    #------------------------------------------------------------------------------
    parser_group = subparsers.add_parser(
        "group",
        help="Load entire group"
    )
    parser_group.add_argument(
        "group",
        help="Subsystem name (e.g. core, f2)"
    )
    parser_group.add_argument(
        "date_from",
        help="Start date (YYYY/MM/DD)"
    )
    parser_group.add_argument(
        "date_to",
        help="End date (YYYY/MM/DD)"
    )
    
    args = parser.parse_args()


    if args.command == "list":
        print("\nAvailable groups and subsystems:\n")
        print_tree(systems_dict)
        print("")
        return

    if args.command == "system":
        print("============================================================")
        print(f"Loading data for system: {args.systems}\n")
        print("From:", args.date_from)
        print("To:", args.date_to)
        print("")
        print("============================================================")
        pipelines_ids = create_pipeline_file(systems_dict, args.systems)
        handle_docker(env, pipelines_ids, args.date_from, args.date_to)
        print("COMPLETED. Exiting...")
        return 0

    if args.command == "group":
        print("============================================================")
        print(f"Loading data for group: {args.group}\n")
        print("From:", args.date_from)
        print("To:", args.date_to)
        print("")
        print("============================================================")
        group_systems = ",".join(systems_dict.get(args.group, {}).keys())
        pipelines_ids = create_pipeline_file(systems_dict, group_systems)
        handle_docker(env, pipelines_ids, args.date_from, args.date_to)
        print("COMPLETED. Exiting...")
        return 0


    parser.print_help()


if __name__ == "__main__":
    main()

