import yaml
import re
import subprocess
from datetime import datetime, timedelta
import calendar
import os
import re


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
        groupedDatesArray.append([str(year), str(month), ",".join(days)])

    return groupedDatesArray


def executeDockerCompose(date,envDic):
    try:
        os.environ['ES01_PORT']= envDic.get('ES01_PORT')
        os.environ['LS_TIMEZONE']= envDic.get('LS_TIMEZONE')
        os.environ['LOGS_PATH']= envDic.get('LOGS_PATH')
        os.environ['DATA_PATH']= envDic.get('DATA_PATH')
        os.environ['DAY'] = "{"+date[2]+"}"
        os.environ['MONTH'] = date[1]
        os.environ['YEAR'] = date[0]
        subprocess.run(['/bin/docker','compose', '-f', '../ls02.yml', 'up', 'logstash_02'] ,check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker Compose: {e}")

def mainMenu(subsystemsDic):
    envDic= getEnvironment()
    while True:
        print("\nOptions:")
        print("Enter options and arguments:\n-l locations\n-s subsystems\n-i start day\n-f end date\nExample: '-l cpo sbf -s tcs vii -i 05/20/2023 -f 05/21/2023'")
        print("Type 'exit' to end the program.")
        userInput = input("Enter your options: ").lower()

        if userInput == 'exit':
            print("Exiting the program...")
            break

        options = parseInput(userInput)
        createPipelinesFile(subsystemsDic, options['l'], options['s'])
        if options['i'] and options['f']:

            dates = getDatesGroupedByMonth(options['i'][0], options['f'][0])
            for date in dates:
                executeDockerCompose(date,envDic)
        else:
            executeDockerCompose([ '*', '*', '*'])

subsystemsDic = getSubsystems()
mainMenu(subsystemsDic)
