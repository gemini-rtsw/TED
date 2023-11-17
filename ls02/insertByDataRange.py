import yaml
import re
import subprocess
from datetime import datetime, timedelta
import os

def getSubsystems():
    subsystemsDic = {}
    try:
        with open("./config/pipelines.yml", "r") as file:
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

def createFile(subsystemsDic, locations, subsystems):
    if not locations:
        locations = subsystemsDic.keys()

    with open("./config/pipelines.yml", 'w') as file:
        for location in locations:
            subsystemsToInclude = subsystems if subsystems else subsystemsDic[location].keys()
            for subsystem in subsystemsToInclude:
                pipeline = subsystemsDic.get(location, {}).get(subsystem)
                if pipeline:
                    file.write(f"- pipeline.id: {pipeline['pipeline.id']}\n")
                    file.write(f"  pipeline.workers: {pipeline['pipeline.workers']}\n")
                    file.write(f"  path.config: {pipeline['path.config']}\n")
                    file.write(f"  queue.type: {pipeline['queue.type']}\n")
                    file.write(f"  queue.max_bytes: {pipeline['queue.max_bytes']}\n\n")
def parseInput(userInput):
    pattern = r'-(l|s|i|f) ([^\-]+)'
    matches = re.findall(pattern, userInput)

    options = {'l': None, 's': None, 'i': None, 'f': None}
    for option, argument in matches:
        options[option] = argument.split()
    return options

def getDatesInRange(startDate, endDate):
    startDate = datetime.strptime(startDate,"%m/%d/%Y").date()
    endDate = datetime.strptime(endDate, "%m/%d/%Y").date()

    dates = []
    while startDate <= endDate:
        dates.append([str(startDate.month),str(startDate.day),str(startDate.year)[2:]])
        startDate += timedelta(days=1)

    return dates

def dockerCompose(date):
    try:
        os.environ['DAY'] = date[1]
        os.environ['MONTH'] = date[0]
        os.environ['YEAR'] = date[2]
        subprocess.run(['/usr/local/bin/docker-compose', '-f', '../docker-compose.yml', 'up', 'logstash_02'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing Docker Compose: {e}")

def mainMenu(subsystemsDic):
    while True:
        print("\nOptions:")
        print("Enter options and arguments:\n-l locations\n-s subsystems\n-i start day\n-f end date\nExample: '-l cpo sbf -s tcs vii -i 05/20/2023 -f 05/21/2023'")
        print("Type 'exit' to end the program.")
        userInput = input("Enter your options: ").lower()

        if userInput == 'exit':
            print("Exiting the program...")
            break

        options = parseInput(userInput)
        createFile(subsystemsDic, options['l'], options['s'])
        if options['i'] and options['f']:
            dates = getDatesInRange(options['i'][0], options['f'][0])
            for date in dates:
                dockerCompose(date)
        else:
            dockerCompose([ '*', '*', '*'])

subsystemsDic = getSubsystems()
mainMenu(subsystemsDic)
