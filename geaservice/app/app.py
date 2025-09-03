# Standard library imports
import sys
import logging
import threading
import json

# Related third-party imports
from flask import Flask,jsonify,request
from waitress import serve
import xmlrpc.client as XmlClient
from flask_cors import CORS
from cache import initializeCache, updateArchivesCache, updateChannelsCache
from utils import setNPoints, processChannels, identifyArchive
from fetchValues import fetchValues

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Initialize semaphore
sem = threading.Semaphore()
lock = threading.Lock()

# Initialize the XML-RPC client
gea = XmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')

archivesCache, channelsByArchiveCache = initializeCache(gea)

@app.route("/updateArchives", methods=['POST'])
def updateArchives():
    global archivesCache

    try:
        with lock:
            archivesCache = updateArchivesCache(gea)
            logging.info("Archives cache updated successfully.")
        return jsonify({"message": "Archives updated successfully."}), 200
    except Exception as e:
        logging.error(f"Failed to update archives: {e}")
        return jsonify({"error": "Failed to update archives."}), 500

@app.route("/updateChannels", methods=['POST'])
def updateChannels():
    global channelsByArchiveCache

    try:
        with lock:
            channelsByArchiveCache = updateChannelsCache(gea,archivesCache)
            logging.info("Channels by archive cache updated successfully.")
        return jsonify({"message": "Channels updated successfully."}), 200
    except Exception as e:
        logging.error(f"Failed to update channels: {e}")
        return jsonify({"error": "Failed to update channels."}), 500

@app.route("/archives", methods=['GET'])
def getArchives():
    with lock:
        return jsonify({"names": list(archivesCache.keys())})

@app.route("/channels", methods=['GET'])
def getChannels():
    with lock:
        archiveName = request.args.get('archiveName')
        channelsTmp = channelsByArchiveCache.get(archiveName, "Not Found")
        if channelsTmp == "Not Found":
            logging.warning(f"Channels for archive '{archiveName}' not found.")
            channelsTmp = [["None","None","None"]]
        channels = list(map(lambda x: x[0], channelsTmp))
        return jsonify({"channels": channels})

@app.route("/pvSelector", methods=['GET'])
def pvSelector():
    try:
        logging.info("Loading PV selector data from 'PVselector.json'.")
        with open('../jsons/PVselector.json') as file:
            pvSelectorData = json.load(file)
        logging.info("Successfully loaded PV selector data.")
        return jsonify(pvSelectorData)
    except Exception as e:
        logging.error(f"Failed to load PV selector data: {e}")
        return jsonify({}) 

@app.route("/pvTree", methods=['GET'])
def pvTree():
    try:
        logging.info("Loading PV selector data from 'PVselector.json'.")
        with open(f"../jsons/pvTree.json") as file:
            pvSelectorData = json.load(file)
        logging.info("Successfully loaded PV selector data.")
        return jsonify(pvSelectorData)
    except Exception as e:
        logging.error(f"Failed to load PV selector data: {e}")
        return jsonify({}) 

@app.route("/allSubsystems", methods=['GET'])
def allSubsystems():
    try:
        logging.info("Loading all subsystems data from 'allSubsystems.json'.")
        with open('../jsons/allSubsystems.json') as file:
            dataSubs = json.load(file)
        logging.info("Successfully loaded all subsystems data.")
        return jsonify(dataSubs)
    except Exception as e:
        logging.error(f"Failed to load all subsystems data: {e}")
        return jsonify({}) 

@app.route("/getLinkPage", methods=['GET'])
def getLinkPage():
    subsystem = request.args.get('subsystem')

    try:
        logging.info(f"Loading link page for subsystem: {subsystem}.")
        with open(f'../linkPages/{subsystem}.html', 'r') as file:
            content = file.read()
        logging.info(f"Successfully loaded link page for subsystem: {subsystem}.")
        return content
    except FileNotFoundError:
        logging.error(f"Link page for subsystem '{subsystem}' not found.")
        return {}
    except Exception as e:
        logging.error(f"Failed to load link page for subsystem '{subsystem}': {e}")
        return {}

@app.route("/values", methods=['GET'])
def getValues():
    dateFrom = int(int(request.args.get('from'))/1000)
    dateTo = int(int(request.args.get('to'))/1000)
    archiveName = request.args.get('archive')
    channels = request.args.get('channel')
    valueMode = int(request.args.get('value_mode'))
    nPoints = request.args.get('n_points')

    nPoints = int(setNPoints(valueMode, dateFrom, dateTo, nPoints))

    channelsList = processChannels(channels)
    channelsListByArchiveDict = identifyArchive(channelsByArchiveCache,channelsList)
    output = []
    if channelsList:
        try:
            with lock:
                logging.info(f"Retrieval mode is {valueMode}.")
                logging.info(f"Retrieving values for channels: {channelsList}.")
                output = fetchValues(gea, channelsListByArchiveDict, dateFrom, dateTo, nPoints, valueMode,archivesCache)
                logging.info("Successfully retrieved values.")
        except Exception as e:
            logging.error(f"Failed to retrieve values: {e}")

    return jsonify({"values": output})

if __name__ == '__main__':
    app.run(debug=True)
