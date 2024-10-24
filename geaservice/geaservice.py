from flask import Flask, jsonify, request
import xmlrpc.client as XmlClient
import sys
import threading
import logging
import json
from enum import Enum
from waitress import serve
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize semaphore
sem = threading.Semaphore()

# Initialize Flask application
app = Flask(__name__)

# Initialize the XML-RPC client
gea = XmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')

archivesCache = {}
channelsByArchiveCache = {}

class DataType(Enum):
    STRING = 0
    ENUM = 1
    INT = 2
    FLOAT = 3

def initializeCache():
    global archivesCache
    global channelsByArchiveCache

    # Inicializar archivesCache
    if os.path.exists("archives.json"):
        logging.debug("File 'archives.json' exists.")
        try:
            with open("archives.json", 'r') as jsonFile:
                archivesCache = json.load(jsonFile)
                logging.info("Successfully loaded archives from file.")
        except Exception as e:
            logging.error(f"Failed to load archives from file: {e}")
            archivesCache = readArchives()  # Fallback si falla la carga
    else:
        logging.debug("File 'archives.json' does not exist.")
        archivesCache = readArchives()

    # Inicializar channelsByArchiveCache
    if os.path.exists("channelsByArchive.json"):
        logging.debug("File 'channelsByArchive.json' exists.")
        try:
            with open("channelsByArchive.json", 'r') as jsonFile:
                channelsByArchiveCache = json.load(jsonFile)
                logging.info("Successfully loaded channels from file.")
        except Exception as e:
            logging.error(f"Failed to load channels from file: {e}")
            channelsByArchiveCache = readChannels()  # Fallback si falla la carga
    else:
        logging.debug("File 'channelsByArchive.json' does not exist.")
        channelsByArchiveCache = readChannels()

def readArchives():
    archivesDict = {}
    try:
        logging.info("Retrieving list of archives.")
        archives = gea.archiver.archives()
        for archive in archives:
            archivesDict[archive['name']] = archive['key']
        logging.info("Successfully retrieved archives.")
    except Exception as e:
        logging.error(f"Failed to retrieve archives: {e}")

    # Guardar archivos después de recuperar
    try:
        logging.info("Saving archives to 'archives.json'.")
        with open('archives.json', 'w') as jsonFile:
            json.dump(archivesDict, jsonFile, indent=4)
    except Exception as e:
        logging.error(f"Failed to save archives to file: {e}")
    
    return archivesDict

def readChannels():
    channelsByArchiveDict = {}
    try:
        logging.info("Retrieving channels by archive.")
        for name, key in archivesCache.items():
            logging.debug(f"Processing archive '{name}' (Key: {key})")
            channelNames = ["None"]

            try:
                channels = gea.archiver.names(int(key), "")
                for channel in channels:
                    channelNames.append(channel['name'])
                channelsByArchiveDict[name] = channelNames

            except Exception as channelError:
                logging.error(f"Failed to retrieve channels for '{name}': {channelError}")

        logging.info("Successfully retrieved channels.")
    except Exception as e:
        logging.error(f"Failed to retrieve channels: {e}")

    # Guardar archivos después de recuperar
    try:
        logging.info("Saving channels by archive to 'channelsByArchive.json'.")
        with open('channelsByArchive.json', 'w') as jsonFile:
            json.dump(channelsByArchiveDict, jsonFile, indent=4)
    except Exception as e:
        logging.error(f"Failed to save channels to file: {e}")
    
    return channelsByArchiveDict


@app.route("/updateArchives", methods=['POST'])
def updateArchives():
    global archivesCache 

    try:
        with sem:
            archivesCache = readArchives()  
            logging.info("Archives cache updated successfully.")
        return jsonify({"message": "Archives updated successfully."}), 200
    except Exception as e:
        logging.error(f"Failed to update archives: {e}")
        return jsonify({"error": "Failed to update archives."}), 500

@app.route("/updateChannels", methods=['POST'])
def updateChannels():
    global channelsByArchiveCache 

    try:
        with sem:
            channelsByArchiveCache = readChannels()  
            logging.info("Channels by archive cache updated successfully.")
        return jsonify({"message": "Channels updated successfully."}), 200  
    except Exception as e:
        logging.error(f"Failed to update channels: {e}")
        return jsonify({"error": "Failed to update channels."}), 500  


@app.route("/archives", methods=['GET'])
def getArchives():
    with sem:
        return jsonify({"names": list(archivesCache.keys())})

@app.route("/channels", methods=['GET'])
def getChannels():
    with sem:
        archiveName = request.args.get('archiveName')
        channels = channelsByArchiveCache.get(archiveName, "Not Found")
        if channels == "Not Found":
            logging.warning(f"Channels for archive '{archiveName}' not found.")
        return jsonify({"channels": channels})

@app.route("/values", methods=['GET'])
def getValues():
    dateFrom = request.args.get('from')
    dateTo = request.args.get('to')
    archiveName = request.args.get('archive')
    channel = request.args.get('channel')
    valueMode = request.args.get('value_mode')
    nPoints = request.args.get('n_points')
    archiveKey = archivesCache.get(archiveName, 10)
    logging.debug(f"Retrival mode is {valueMode}.") 
    try:
        nPoints = int(nPoints)
        if nPoints > 10000:
            nPoints = 10000
        logging.info(f"Setting number of points to {nPoints}.")
    except ValueError:
        nPoints = 3000
        logging.warning("Invalid 'nPoints' value; defaulting to 3000.")

    channelsList = []

    if ',' in channel:
        channelsList = [chan.strip() for chan in channel.split(',') if chan.strip() and chan not in ["", " ", "None"]]
    else:
        if channel.strip() and channel not in ["", " ", "None"]:
            channelsList = [channel.strip()]

    output = {}
    if channelsList:
        try:
            logging.info(f"Retrieving values for channels: {channelsList}.")
            sem.acquire()
            geaRecord = gea.archiver.values(
                int(archiveKey), channelsList,
                int(int(dateFrom) / 1000), 0,
                int(int(dateTo) / 1000), 0,
                int(nPoints),
                int(valueMode)
            )
            output = geaRecord
            logging.info("Successfully retrieved values.")
        except Exception as e:
            logging.error(f"Failed to retrieve values: {e}")
        finally:
            sem.release()
    else:
        output = []
        logging.warning(f"No valid channels provided for value retrieval: {channelsList}.")

    sys.stdout.flush()
    return {"values": output}

@app.route("/pvSelector", methods=['GET'])
def pvSelector():
    try:
        logging.info("Loading PV selector data from 'PVselector.json'.")
        with open('PVselector.json') as file:
            data = json.load(file)
        logging.info("Successfully loaded PV selector data.")
        return data
    except Exception as e:
        logging.error(f"Failed to load PV selector data: {e}")
        return {}

@app.route("/allSubsystems", methods=['GET'])
def allSubsystems():
    try:
        logging.info("Loading all subsystems data from 'allSubsystems.json'.")
        with open('allSubsystems.json') as file:
            dataSubs = json.load(file)
        logging.info("Successfully loaded all subsystems data.")
        return dataSubs
    except Exception as e:
        logging.error(f"Failed to load all subsystems data: {e}")
        return {}

@app.route("/allChannels", methods=['GET'])
def allChannels():
    try:
        logging.info("Loading all channels data from 'channels.json'.")
        with open('channels.json') as file:
            dataChannels = json.load(file)
        logging.info("Successfully loaded all channels data.")
        return dataChannels
    except Exception as e:
        logging.error(f"Failed to load all channels data: {e}")
        return {}

if __name__ == '__main__':
    logging.info("Starting the server.")
    initializeCache()
    serve(app, host='0.0.0.0', port=8000, threads=50)
    logging.info("Server is running on port 8000.")
