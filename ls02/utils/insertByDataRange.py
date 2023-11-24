import yaml
import re
import subprocess
from datetime import datetime, timedelta
import calendar
import os
import re
import time
import json


def getEnvironment():
    envDic={}
    try:
        with open("../../.env", "r") as file:
            for line in file:
                field=re.match("(.*)=(.*)",line)
                if field:
                    key= field.group(1)
                    value = field.group(2)
                    envDic[key]=value
        return envDic
    except Exception as exc:
        print(f"Error loading environment file: {exc}")
        return envDic

def getSubsystems():
    subsystemsDic = {}
    try:
        with open("../../ls01/config/pipelines.yml", "r") as file:
            pipelines = yaml.safe_load(file)
    except (yaml.YAMLError, IOError) as exc:
        print(f"Error loading configuration file: {exc}")
        return subsystemsDic

    for pipeline in pipelines:
        pipelineDetails = pipeline["pipeline.id"].split("-")
        location, name = pipelineDetails[:2]
        if len(pipelineDetails) > 3:
            name += "-" + pipelineDetails[2]
        subsystemsDic.setdefault(location, {})[name] = pipeline

    return subsystemsDic

def createPipelinesFile(subsystemsDic, locations, subsystems):
    pipelinesNames=[]
    if not locations:
        locations = subsystemsDic.keys()

    with open("../config/pipelines.yml", 'w') as file:
        for location in locations:
            if subsystemsDic.get(location):
                subsystemsToInclude = subsystems if subsystems else subsystemsDic[location].keys()
                for subsystem in subsystemsToInclude:
                    pipeline = subsystemsDic.get(location, {}).get(subsystem)
                    if pipeline:
                        file.write(f"- pipeline.id: {pipeline['pipeline.id']}\n")
                        file.write(f"  pipeline.workers: {pipeline['pipeline.workers']}\n")
                        file.write(f"  path.config: \"{pipeline['path.config']}\"\n")
                        file.write(f"  queue.type: {pipeline['queue.type']}\n")
                        file.write(f"  queue.max_bytes: {pipeline['queue.max_bytes']}\n\n")
                        pipelinesNames.append(f'{location}-{subsystem}-read')
    return pipelinesNames

def parseInput(userInput):
    pattern = r'-(l|s|i|f)(?: ([^\-]+))?'
    matches = re.findall(pattern, userInput)

    options = {'l': None, 's': None, 'i': None, 'f': None}
    for option, argument in matches:
            options[option] = argument.split()
    return options

def getDatesGroupedByMonth(startDate, endDate):
    try:
        startDate = datetime.strptime(startDate, "%Y/%m/%d").date()
        endDate = datetime.strptime(endDate, "%Y/%m/%d").date()
    except Exception as exc:
        print(f"Error de formato de fecha: {exc}")
        return []

    groupedDates = {}
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
        formattedYear = f"{year:04d}"
        formattedMonth = f"{month:02d}"
        formattedDays = [f"{day:02d}" for day in days]
        groupedDatesArray.append([formattedYear, formattedMonth, "{" + ",".join(formattedDays) + "}"])
    return groupedDatesArray


def dockerComposeUp(date,envDic):
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
        print(f"Error executing Docker Compose: {e}")

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
                process = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
                output = process.stdout
                if (output):
                    statsPipeline = json.loads(output.decode())

                    state = statsPipeline.get('pipelines',{}).get(pipelineName,{}).get('flow', {})
                    if state:
                        currentState = state.get('output_throughput', {}).get('current', -1)
                        if float(currentState) == 0.0:
                            print(f'Pipeline finished: {pipelineName}')
                            pipelinesFinished.add(pipelineName)

            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                print(f"Error processing pipeline {pipelineName}: {e}")

        time.sleep(5)



def dockerComposeDown():
    try:
        subprocess.run(['/bin/docker','rm', '-f', 'ls02'] ,check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker Compose: {e}")


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
                    print("Example: '-l cpo sbf -s tcs vii -i 2022/11/25 -f 2022/12/30'")

def mainMenu(subsystemsDic):
    envDic= getEnvironment()
    nowDate= datetime.now().strftime("%Y/%m/%d")
    print("###############################################################")
    print("##  Welcome to the script for ingesting logs by date ranges  ##")
    print("##                                                           ##")
    print("##  Type '-h' for help and 'exit' to terminate the program.  ##")
    print("###############################################################")
    while True:
        userInput = input("\nEnter your options: ").lower()
        if userInput == 'exit':
            print("Exiting the program...")
            break

        if userInput == '-h':
            printHelpMessage()
        else:
            dates=None
            options = parseInput(userInput)
            pipelinesNames=createPipelinesFile(subsystemsDic, options['l'], options['s'])
            if (len(pipelinesNames) > 0):
                if options['i'] and options['f']:
                        dates = getDatesGroupedByMonth(options['i'][0], options['f'][0])
                elif options['i']:
                        dates = getDatesGroupedByMonth(options['i'][0], nowDate)
                else:
                    printInvalidInputMessage()
                if dates:
                    for date in dates:
                        dockerComposeUp(date,envDic)
                        verifyFinished(pipelinesNames)
                        dockerComposeDown()
            else:
                    printInvalidInputMessage()

subsystemsDic = getSubsystems()
mainMenu(subsystemsDic)
