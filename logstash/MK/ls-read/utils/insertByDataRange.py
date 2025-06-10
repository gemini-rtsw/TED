#!/bin/python3

import time
import yaml
import re
import subprocess
import logging
from datetime import datetime, timedelta
import calendar
import os
import json

# --- Logger Setup ---
def setupLogger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='InsertByDataRange.log',
        filemode='a'
    )

# --- Retry Helper ---
def retryCommand(command, retries=3, delay=3):
    for attempt in range(retries):
        try:
            subprocess.run(command, check=True)
            return
        except subprocess.CalledProcessError as e:
            logging.warning(f"Retry {attempt + 1}/{retries} failed: {e}")
            time.sleep(delay)
    logging.error(f"Command failed after {retries} retries: {' '.join(command)}")

# --- Environment Handling ---
def loadEnvironment(path="../../../../.env"):
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
def loadSubsystems(group):
    configPath=f"../../ls-{group}/config/pipelines.yml"
    subsystems = {}
    try:
        with open(configPath, "r") as file:
            pipelines = yaml.safe_load(file)
        for pipeline in pipelines:
            parts = pipeline["pipeline.id"].split("-")
            location, name = parts[:2]
            if len(parts) > 3:
                name += f"-{parts[2]}"
            pipeline['pipeline.id'] = f"{location}-{name}-read"
            subsystems.setdefault(group, {})[name] = pipeline
    except Exception as exc:
        logging.error(f"Error loading configuration file: {exc}")
    return subsystems

def createPipelinesFile(subsystems, groups, subsystemsFilter, outputPath="../config/pipelines.yml"):
    pipelineNames = []
    groups =  groups or subsystems.keys()
    try:
        with open(outputPath, 'w') as file:
            for group in groups:
                if group in subsystems:
                    filteredSubs = subsystemsFilter or subsystems[group].keys()
                    for subsystem in filteredSubs:
                        print("subsystem", subsystem)
                        pipeline = subsystems[group].get(subsystem)
                        print("pipeline: ", pipeline)
                        if pipeline:
                            file.write(f"- pipeline.id: {pipeline['pipeline.id']}\n")
                            file.write(f"  pipeline.workers: {pipeline['pipeline.workers']}\n")
                            file.write(f"  path.config: \"{pipeline['path.config']}\"\n")
                            file.write(f"  queue.type: {pipeline['queue.type']}\n")
                            file.write(f"  queue.max_bytes: {pipeline['queue.max_bytes']}\n\n")
                            pipelineNames.append(pipeline['pipeline.id'])
    except Exception as exc:
        logging.error(f"Error creating pipelines file: {exc}")

    return pipelineNames

# --- Input Parsing ---
def parseInput(userInput):
    matches = re.findall(r'-(l|s|i|f) ("[^\"]*"|\S+)', userInput)
    options = {'l': None, 's': None, 'i': None, 'f': None}
    for opt, arg in matches:
        cleaned = arg.strip('"')
        options[opt] = cleaned.split()
    print(options)
    return options

# --- Date Handling ---
def getDatesByMonth(startDate, endDate):
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

# --- Docker Actions ---
def dockerUp(date, env):
    print(f"\n### Logs ingestion for {date[3]} {date[0]} ###\n")
    print(date)
    os.environ.update({
        'HOST01_IP': env.get('HOST01_IP'),
        'ES01_PORT': env.get('ES01_PORT', ''),
        'LS_TIMEZONE': env.get('LS_TIMEZONE', ''),
        'LOGS_PATH': env.get('LOGS_PATH', ''),
        'DATA_PATH': env.get('DATA_PATH', ''),
        'DAY': date[2],
        'MONTH': date[1],
        'YEAR': date[0],
    })
    retryCommand(['/bin/docker', 'compose', '-f', '../ls-read.yml', 'up', '-d', 'ls-read'])

def dockerDown():
    retryCommand(['/bin/docker', 'rm', '-f', 'ls-read'])

# --- Pipeline Monitoring ---
def checkPipelineCompletion(pipelineNames):
    finished = set()
    total = len(pipelineNames)
    print("pipelineNames: ",pipelineNames) 
    print("finished: ", finished)
    print("total", total)
    while len(finished) < total:
        for name in pipelineNames:
            print("name", name)
            if name in finished:
                continue

            cmd = f"docker exec ls-read curl -sS 'http://10.1.76.15:8999/_node/stats/pipelines/{name}'"
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
                    print(f"{m}: current={value} → {comparison}")
                    if not comparison:
                        flowCondition = False

                eventsIn = events.get('in', 0)
                print("eventsIn", eventsIn)
                eventsOut = events.get('out', 0)
                print("eventsOut", eventsOut)
                eventsCondition = eventsIn == eventsOut
                print("flowCondition", flowCondition)
                print("eventsCondition", eventsCondition)
                if flowCondition and eventsCondition:
                    finished.add(name)
                    print(f"✔ Finished: {name}")
            except Exception as e:
                logging.error(f"Error monitoring pipeline {name}: {e}")
        time.sleep(5)

# --- User Messages ---
def printHelp(subsystems=None, showLocations=False, showSubsystems=False):
    print("""
Options:
  -g [groups]     : Example: "core wfs gmos ghost"
  -s [subsystems]    : Example: "tcs vii"
  -i [start date]    : Format: YYYY/MM/DD
  -f [end date]      : Format: YYYY/MM/DD

Example:
  -l core -s tcs -i 2022/11/25 -f 2022/12/30
""")
    if subsystems:
        if showLocations:
            print("\nAvailable Locations:")
            for location in sorted(subsystems.keys()):
                print(f"  - {location}")
        if showSubsystems:
            print("\nAvailable Subsystems:")
            allSubs = set()
            for subs in subsystems.values():
                allSubs.update(subs.keys())
            for name in sorted(allSubs):
                print(f"  - {name}")

def printInvalid():
    print("Invalid input. Use -h for help.")

# --- Main Menu ---
def main():
    setupLogger()
    subsystems = loadSubsystems("wfs")
    print("subsystems", subsystems)
    env = loadEnvironment()
    defaultEndDate = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")

    print("""
###############################################################
##  Welcome to the script for ingesting logs by date ranges  ##
##                                                           ##
##  Type '-h' for help and '-q' to terminate the program.    ##
###############################################################
""")

    while True:
        userInput = input("\nEnter your options: ").strip().lower()
        if userInput in ['-q', '--quit']:
            print("Exiting...")
            break
        if userInput in ['-h', '--help']:
            printHelp(subsystems)
            continue
        if userInput in ['-h -s', '--help --subsystems']:
            printHelp(subsystems, showSubsystems=True)
            continue
        if userInput in ['-h -l', '--help --locations']:
            printHelp(subsystems, showLocations=True)
            continue

        options = parseInput(userInput)
        print("OPTIONS", options)
        pipelines = createPipelinesFile(subsystems, options['l'], options['s'])
        print("PIPELINES", pipelines)
        if pipelines and options['i']:
            end = options['f'][0] if options['f'] else defaultEndDate
            for datesByMonth in getDatesByMonth(options['i'][0], end):
                print(datesByMonth)
                print("\nPreparing to run the following pipelines:")
                for p in pipelines:
                    print(f"  - {p}")
                dockerUp(datesByMonth, env)
                checkPipelineCompletion(pipelines)
                dockerDown()
        else:
            printInvalid()

if __name__ == "__main__":
    main()

