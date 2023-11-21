import yaml
import re
import subprocess
from datetime import datetime, timedelta
import calendar
import os
import re
import time


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
    except (yaml.YAMLError, IOError) as exc:
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
    nPipelines=0
    if not locations:
        locations = subsystemsDic.keys()

    with open("../config/pipelines.yml", 'w') as file:
        for location in locations:
            subsystemsToInclude = subsystems if subsystems else subsystemsDic[location].keys()
            for subsystem in subsystemsToInclude:
                pipeline = subsystemsDic.get(location, {}).get(subsystem)
                if pipeline:
                    file.write(f"- pipeline.id: {pipeline['pipeline.id']}\n")
                    file.write(f"  pipeline.workers: {pipeline['pipeline.workers']}\n")
                    file.write(f"  path.config: \"{pipeline['path.config']}\"\n")
                    file.write(f"  queue.type: {pipeline['queue.type']}\n")
                    file.write(f"  queue.max_bytes: {pipeline['queue.max_bytes']}\n\n")
                    nPipelines+=1;
    return nPipelines

def parseInput(userInput):
    pattern = r'-(l|s|i|f) ([^\-]+)'
    matches = re.findall(pattern, userInput)

    options = {'l': None, 's': None, 'i': None, 'f': None}
    for option, argument in matches:
        options[option] = argument.split()
    return options

def getDatesGroupedByMonth(startDate, endDate):
    startDate = datetime.strptime(startDate, "%m/%d/%Y").date()
    endDate = datetime.strptime(endDate, "%m/%d/%Y").date()

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
        days = [str(day) for day in days]
        groupedDatesArray.append([str(year), str(month), "{"+",".join(days)+"}"])

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
        subprocess.run(['/bin/docker','compose', '-f', '../ls02.yml', 'up','-d','logstash_02'] ,check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker Compose: {e}")

def verifyFinished(nPipelines):
    try:
        state=False
        while not state:
            rawLogs=subprocess.run(['/bin/docker','logs', 'ls02'],stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,check=True).stdout.split('\n')
            state=finishedPipelines(rawLogs,nPipelines)
            time.sleep(10)
    except subprocess.CalledProcessError as e:
        print(f"Error reading Docker logs: {e}")

def finishedPipelines(rawLogs,nPipelines):
    state= False
    count=0
    for rawLog in rawLogs:
        result=re.match('(\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d{3}\]\[INFO \]\[logstash\.javapipeline    \]\[[a-z-]+\] Pipeline terminated \{"pipeline.id"=>"[a-z-]+"\})',rawLog)
        if (result):
            count+=1
            if(count==nPipelines):
                state=True
    return state

def dockerComposeDown():
    try:
        subprocess.run(['/bin/docker','rm', '-f', 'ls02'] ,check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker Compose: {e}")

def mainMenu(subsystemsDic):
    envDic= getEnvironment()
    nowDate= datetime.now().strftime("%m/%d/%Y")
    while True:
        print("\nOptions:")
        print("Enter options and arguments:\n-l locations\n-s subsystems\n-i start day\n-f end date\nExample: '-l cpo sbf -s tcs vii -i 05/20/2023 -f 05/21/2023'")
        print("Type 'exit' to end the program.")
        userInput = input("Enter your options: ").lower()

        if userInput == 'exit':
            print("Exiting the program...")
            break

        options = parseInput(userInput)
        nPipelines=createPipelinesFile(subsystemsDic, options['l'], options['s'])
        if options['i'][0] and options['f'][0]:
            dates = getDatesGroupedByMonth(options['i'][0], options['f'][0])
        else:
            dates = getDatesGroupedByMonth("01/01/2010", nowDate)
        for date in dates:
                dockerComposeUp(date,envDic)
                verifyFinished(nPipelines)
                dockerComposeDown()

subsystemsDic = getSubsystems()
mainMenu(subsystemsDic)
