import time
import yaml
import re
import subprocess
import logging
from datetime import datetime, timedelta
import calendar
import os
import json

def setupLogger():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='InsertByDataRange.log',
                        filemode='a')


def getEnvironment():
    envDict = {}
    try:
        with open("../../.env", "r") as file:
            for line in file:
                key, _, value = line.partition("=")
                envDict[key.strip()] = value.strip()
    except Exception as exc:
        logging.error(f"Error loading environment file: {exc}")
    return envDict

def getSubsystems():
    subsystemsDict = {}
    try:
        with open("../../ls01/config/pipelines.yml", "r") as file:
            pipelines = yaml.safe_load(file)
        for pipeline in pipelines:
            pipelineDetails = pipeline["pipeline.id"].split("-")
            location, name = pipelineDetails[:2]
            if len(pipelineDetails) > 3:
                name += "-" + pipelineDetails[2]
            subsystemsDict.setdefault(location, {})[name] = pipeline
    except (yaml.YAMLError, IOError) as exc:
        logging.error(f"Error loading configuration file: {exc}")
    return subsystemsDict


def createPipelinesFile(subsystemsDict, locations, subsystems):
    pipelinesNames = []
    if not locations:
        locations = subsystemsDict.keys()

    try:
        with open("../config/pipelines.yml", 'w') as file:
            for location in locations:
                if subsystemsDict.get(location):
                    subsystemsToInclude = subsystems if subsystems else subsystemsDict[location].keys()
                    for subsystem in subsystemsToInclude:
                        pipeline = subsystemsDict.get(location, {}).get(subsystem)
                        if pipeline:
                            file.write(f"- pipeline.id: {pipeline['pipeline.id']}\n")
                            file.write(f"  pipeline.workers: {pipeline['pipeline.workers']}\n")
                            file.write(f"  path.config: \"{pipeline['path.config']}\"\n")
                            file.write(f"  queue.type: {pipeline['queue.type']}\n")
                            file.write(f"  queue.max_bytes: {pipeline['queue.max_bytes']}\n\n")
                            pipelinesNames.append(f'{location}-{subsystem}-read')
    except Exception as exc:
        logging.error(f"Error creating pipelines file: {exc}")
    return pipelinesNames

def parseInput(userInput):
    pattern = r'-(l|s|i|f) ([^\-]+)'
    matches = re.findall(pattern, userInput)

    options = {'l': None, 's': None, 'i': None, 'f': None}
    for option, argument in matches:
            options[option] = argument.split()
    return options

def getDatesGroupedByMonth(startDate, endDate):
    groupedDates = {}
    try:
        startDate = datetime.strptime(startDate, "%Y/%m/%d").date()
        endDate = datetime.strptime(endDate, "%Y/%m/%d").date()
    except ValueError as exc:
        printInvalidInputMessage()
        logging.error(f"Date format error: {exc}")
        return groupedDates

    while startDate <= endDate:
        yearMonthKey = (startDate.year, startDate.month)
        if yearMonthKey not in groupedDates:
            groupedDates[yearMonthKey] = []

        lastDayOfMonth = calendar.monthrange(startDate.year, startDate.month)[1]
        if startDate.day <= lastDayOfMonth:
            groupedDates[yearMonthKey].append(startDate.day)

        startDate += timedelta(days=1)

    groupedDatesArray = []
    for (year, month), days in groupedDates.items():
        monthName = calendar.month_name[int(month)][0:3]
        formattedYear = f"{year:04d}"
        formattedMonth = f"{month:02d},{monthName}"
        formattedDays = [f"{day:02d}" for day in days]
        groupedDatesArray.append([formattedYear, "{" + formattedMonth + "}", "{" + ",".join(formattedDays) + "}", monthName])
    return groupedDatesArray


def dockerComposeUp(date,envDic):
    print(f"\n##############################################")
    print(f"##     Logs ingestion as of {date[3]} {date[0]}        ##")
    print(f"##############################################\n")
    try:
        os.environ['LOGSTASH_MODE']= "read"
        os.environ['ES01_PORT']= envDic.get('ES01_PORT')
        os.environ['LS_TIMEZONE']= envDic.get('LS_TIMEZONE')
        os.environ['LOGS_PATH']= envDic.get('LOGS_PATH')
        os.environ['DATA_PATH']= envDic.get('DATA_PATH')
        os.environ['DAY'] = date[2]
        os.environ['MONTH'] = date[1]
        os.environ['YEAR'] = date[0][2:]
        subprocess.run(['/bin/docker','compose', '-f', '../ls02.yml', 'up','-d','logstash02'] ,check=True)
    except subprocess.CalledProcessError as e:
        print ("Error executing Docker Compose")
        logging.error(f"Error executing Docker Compose: {e}")

def verifyFinished(pipelinesNames):
    nPipelines = len(pipelinesNames)
    pipelinesFinished = set()

    while len(pipelinesFinished) < nPipelines:
        for pipelineName in pipelinesNames:
            if pipelineName in pipelinesFinished:
                continue

            cmdPipeline = f"curl -sS 'http://localhost:9600/_node/stats/pipelines/{pipelineName}'"
            cmd = f"docker exec ls02 /bin/sh -c '{cmdPipeline}'"

            try:
                process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if process.returncode != 0:
                    raise Exception(process.stderr)
                else:
                    statsPipeline = json.loads(process.stdout.decode())
                    pipelineStats = statsPipeline.get('pipelines', {}).get(pipelineName, {}).get('flow', {})

                    if all(pipelineStats.get(metric, {}).get('current', -1) == 0.0 for metric in
                        ['output_throughput', 'filter_throughput', 'input_throughput',
                            'queue_backpressure', 'worker_concurrency',
                            'queue_persisted_growth_bytes', 'queue_persisted_growth_events']):
                        pipelinesFinished.add(pipelineName)
                        print(f'Pipeline finished: {pipelineName}')

            except json.JSONDecodeError:
                logging.error(f"Error parsing JSON response from pipeline {pipelineName}")
            except Exception as e:
                logging.error(f"Error while processing the pipeline {pipelineName}: {e}")

        time.sleep(5)



def dockerComposeDown():
    try:
        subprocess.run(['/bin/docker', 'rm', '-f', 'ls02'])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing Docker Compose: {e}")


def printHelpMessage():
            print("-l [locations] : Specify locations separated by spaces. Example: 'cpo sbf'")
            print("-s [subsystems] : Specify subsystems separated by spaces. Example: 'tcs vii'")
            print("-i [start date] : Specify the start date in YYYY/MM/DD format. Example: '2022/11/25'")
            print("-f [end date] : Specify the end date in YYYY/MM/DD format. Example: '2022/12/30'")
            print("Complete input example: '-l cpo sbf -s tcs vii -i 2022/11/25 -f 2022/12/30'")

def printInvalidInputMessage():
            print("\nInput not recognized or missing options.")
            print("Please make sure to enter the options correctly.")
            print("Valid options are -l, -s, -i, -f")
            print("Dates should be in the format YYYY/MM/DD.")
            print("Example: '-l cpo sbf -s tcs vii -i 2022/11/25 -f 2022/12/30'")

def mainMenu(subsystemsDict):
    envDict= getEnvironment()
    yesterday=datetime.now()-timedelta(days=1)
    yesterdayDate=yesterday.strftime("%Y/%m/%d")
    print("###############################################################")
    print("##  Welcome to the script for ingesting logs by date ranges  ##")
    print("##                                                           ##")
    print("##  Type '-h' for help and '-q' to terminate the program.    ##")
    print("###############################################################")
    while True:
        userInput = input("\nEnter your options: ").lower()
        if userInput == '-q':
            print("Exiting the program...")
            break

        if userInput == '-h':
            printHelpMessage()
        else:
            dates=None
            options = parseInput(userInput)
            pipelinesNames=createPipelinesFile(subsystemsDict, options['l'], options['s'])
            if (len(pipelinesNames) > 0):
                if options['i'] and options['f']:
                        dates = getDatesGroupedByMonth(options['i'][0], options['f'][0])
                elif options['i']:
                        dates = getDatesGroupedByMonth(options['i'][0], yesterdayDate)
                else:
                    printInvalidInputMessage()
                if dates:
                    for date in dates:
                        dockerComposeUp(date,envDict)
                        verifyFinished(pipelinesNames)
                        dockerComposeDown()
            else:
                    printInvalidInputMessage()

if __name__ == "__main__":
    setupLogger()
    subsystemsDict = getSubsystems()
    mainMenu(subsystemsDict)
