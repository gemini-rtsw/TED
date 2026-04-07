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


# --- Logger Setup ---
def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='insertLogs.log',
        filemode='a'
    )

# --- Retry Helper ---
def retry_cmd(env_vars,command, retries=3, delay=3):
    for attempt in range(retries):
        try:
            subprocess.run(command, check=True, env=env_vars)
            return
        except subprocess.CalledProcessError as e:
            logging.warning(f"Retry {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    logging.error(f"Command failed after {retries} retries: {' '.join(command)}")

# --- Environment Handling ---
def load_env(path="../../CP/.env"):
    envDict = {}
    try:
        with open(path, "r") as file:
            for line in file:
                key, _, value = line.partition("=")
                envDict[key.strip()] = value.strip()
    except Exception as exc:
        logging.error(f"Error loading environment file: {exc}")
    return envDict

def load_systems():
    base_dir = Path("../../../logstash/CP")
    dict_pipelines = {}
    for cfg in base_dir.glob("*/pipeline/*/*read.cfg"):
        top = cfg.parents[2].name
        sub = cfg.parent.name
        dict_pipelines.setdefault(top, []).append(sub)
    # print(dict_pipelines)
    return dict_pipelines

def print_tree(data):
    for group, files in data.items():
        print(group)
        for name in files:
            print(f"  └─ {name}")


def checkPipelineCompletion(pipelineNames):
    finished = set()

    while len(finished) < len(pipelineNames):
        for name in pipelineNames:
            if name in finished:
                continue
            pipeline_id = f"cp-{name}-read"
            try:
                result = subprocess.run(
                    [
                        "docker", "exec", "ls-read",
                        "curl", "-sS", f"http://localhost:9666/_node/stats/pipelines/{pipeline_id}"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=10
                )

                if result.returncode != 0:
                    logging.error(f"{name}: command failed → {result.stderr.decode()}")
                    continue

                try:
                    stats = json.loads(result.stdout.decode())
                except json.JSONDecodeError:
                    logging.error(f"{name}: invalid JSON response")
                    continue

                pipeline = stats.get("pipelines", {}).get(pipeline_id)

                # Pipeline not found
                if not pipeline:
                    finished.add(name)
                    print(f"\033[93m! Skipping: {name} (path not found)\033[0m")
                    continue

                events = pipeline.get("events", {})
                flow = pipeline.get("flow", {})

                # Flow condition (all zero)
                metrics = [
                    'output_throughput',
                    'filter_throughput',
                    'input_throughput',
                    'queue_backpressure',
                    'queue_persisted_growth_bytes',
                    'queue_persisted_growth_events'
                ]

                flowCondition = all(
                    flow.get(m, {}).get('current', -1) == 0.0
                    for m in metrics
                )

                eventsIn = events.get('in', 0)
                eventsOut = events.get('out', 0)

                eventsCondition = eventsIn == eventsOut

                print(f"{name} → in: {eventsIn}, out: {eventsOut}")
                print(f"{name} → events OK: {eventsCondition}, flow OK: {flowCondition}")

                if flowCondition and eventsCondition:
                    finished.add(name)
                    print(f"\033[92m✔ Finished: {name}\033[0m")
            except subprocess.TimeoutExpired:
                logging.error(f"{name}: timeout")
            except Exception as e:
                logging.error(f"{name}: unexpected error → {e}")
        time.sleep(10)


def handle_docker(env, systems_dict, group, date_from, date_to):
    for dates_by_month in get_dates_by_month(date_from, date_to):
        print(f"INSERTING LOGS FOR {dates_by_month[0]} | {dates_by_month[-1]} | {dates_by_month[2]}")
        print(systems_dict[group])
        docker_up(group, dates_by_month, env)
        container_name = f"{group}-read"
        # watch_pipeline_termination(container_name, group)
        checkPipelineCompletion(systems_dict[group])
        docker_down()

def docker_down():
    retry_cmd(None, ['/bin/docker', 'rm', '-f', 'ls-read'])

def docker_up(group, date, env):
    env.update({
        'DAY': date[2],
        'MONTH': date[1],
        'YEAR': date[0],
        'LS_GROUP': group,
        'LS_READMODE': "read"
    })

    retry_cmd(env,['/bin/docker', 'compose', '-f', './insertLogs.yml', 'up', '-d'])



def main():
    setup_logger()
    systems_dict = load_systems()
    env = load_env()
    # print(systems_dict)
    # print_tree(systems_dict)
    defaultEndDate = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")

    parser = argparse.ArgumentParser(
        description="Insert logs script"
    )

    subparsers = parser.add_subparsers(dest="command")
    #------------------------------------------------------------------------------
    parser_list = subparsers.add_parser(
        "list",
        help="List available systems"
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

    if args.command == "group":
        print("============================================================")
        print(f"Loading data for group: {args.group}\n")
        print("From:", args.date_from)
        print("To:", args.date_to)
        print("")
        print("============================================================")
        handle_docker(env, systems_dict, args.group, args.date_from, args.date_to)
        print("COMPLETED. Exiting...")
        return 0


    parser.print_help()




if __name__ == "__main__":
    main()
