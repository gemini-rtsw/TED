from flask import Flask, request
import xmlrpc.client as XmlClient
import sys
import threading
import json
import logging

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize semaphore
sem = threading.Semaphore()

# Initialize Flask application
app = Flask(__name__)

# Initialize the XML-RPC client
gea = XmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')

@app.route("/archives", methods=['GET'])
def getArchives():
    archivesNameList = []
    archivesKeyList = []

    try:
        logging.info("Attempting to retrieve archives.")
        sem.acquire()
        archives = gea.archiver.archives()
        for archive in archives:
            archivesNameList.append(archive['name'])
            archivesKeyList.append(archive['key'])
        logging.info("Archives retrieved successfully.")
    except Exception as e:
        logging.error(f"Error retrieving archives: {e}")
    finally:
        sem.release()
        return {"names": archivesNameList, "keys": archivesKeyList}

@app.route("/channels", methods=['GET'])
def getChannels():
    try:
        logging.info("Attempting to retrieve channels.")
        sem.acquire()
        archiveKey = request.args.get('archive_key')
        channels = gea.archiver.names(int(archiveKey), "")
        channelNames = ['None']
        for channel in channels:
            channelNames.append(channel['name'])
        logging.info("Channels retrieved successfully.")
    except Exception as e:
        logging.error(f"Error retrieving channels: {e}")
    finally:
        with open('channels.json', 'w') as jsonFile:
            json.dump({"channels": channelNames}, jsonFile, indent=4)
        sem.release()
        return {"channels": channelNames}

@app.route("/values", methods=['GET'])
def getValues():
    dateFrom = request.args.get('from')
    dateTo = request.args.get('to')
    archiveKey = request.args.get('archive')
    channel = request.args.get('channel')
    valueMode = request.args.get('value_mode')
    nPoints = request.args.get('n_points')

    try:
        nPoints = int(nPoints)
        if nPoints > 10000:
            nPoints = 10000
        logging.info(f"Number of points set to {nPoints}.")
    except ValueError:
        nPoints = 3000
        logging.warning("Invalid n_points value; defaulting to 3000.")

    channelsList = []

    if ',' in channel:
        channelsList = [chan.strip() for chan in channel.split(',') if chan.strip() and chan not in ["", " ", "None"]]
    else:
        if channel.strip() and channel not in ["", " ", "None"]:
            channelsList = [channel.strip()]

    output = {}
    if channelsList:
        try:
            logging.info(f"Attempting to retrieve values for channels: {channelsList}.")
            sem.acquire()
            geaRecord = gea.archiver.values(
                int(archiveKey), channelsList,
                int(int(dateFrom) / 1000), 0,
                int(int(dateTo) / 1000), 0,
                int(nPoints),
                int(valueMode)
            )
            output = geaRecord
            logging.info("Values retrieved successfully.")
        except Exception as e:
            logging.error(f"Error retrieving values: {e}")
        finally:
            sem.release()
    else:
        output = []
        logging.warning("No valid channels provided for value retrieval.")

    sys.stdout.flush()
    return {"values": output}

@app.route("/pvSelector", methods=['GET'])
def pvSelector():
    try:
        logging.info("Loading PV selector data.")
        with open('PVselector.json') as file:
            data = json.load(file)
        logging.info("PV selector data loaded successfully.")
        return data
    except Exception as e:
        logging.error(f"Error loading PV selector data: {e}")
        return {}

@app.route("/allSubsystems", methods=['GET'])
def allSubsystems():
    try:
        logging.info("Loading all subsystems data.")
        with open('allSubsystems.json') as file:
            dataSubs = json.load(file)
        logging.info("All subsystems data loaded successfully.")
        return dataSubs
    except Exception as e:
        logging.error(f"Error loading all subsystems data: {e}")
        return {}

@app.route("/allChannels", methods=['GET'])
def allChannels():
    try:
        logging.info("Loading all channels data.")
        with open('channels.json') as file:
            dataChannels = json.load(file)
        logging.info("All channels data loaded successfully.")
        return dataChannels
    except Exception as e:
        logging.error(f"Error loading all channels data: {e}")
        return {}

@app.route("/valuesByPattern", methods=['GET'])
def get_values_by_pattern():
    try:
        archive_key = request.args.get('archive')
        pattern = request.args.get('pattern')
        
        date_from = request.args.get('from')
        date_to = request.args.get('to')
        mode = request.args.get('value_mode')
        n_points = request.args.get('n_points')
        
        sem.acquire()
        channels = gea.archiver.names(int(archive_key),pattern)
        channels_names = []
        for channel in channels:
            channels_names.append(channel['name'])
        
        try:
            n_points = int(n_points)
            if n_points > 10000:
                n_points = 10000
        except:
            n_points = 3000
    
        
        output={}
    
        if channels_names[0] not in [" ",""]:
            try:
                geaRecord = gea.archiver.values(int(archive_key), channels_names,
                                            int(int(date_from)/1000), 0,
                                            int(int(date_to)/1000), 0,
                                            int(n_points),
                                            int(str(mode)))
            except Exception as e:
                print(e)
            finally:
                output=geaRecord
        else:
            output=[]
            sys.stdout.flush()
    except Exception as e:
        print(e)

    finally:
        sem.release()
        return {"values":output}




if __name__ == '__main__':
    logging.info("Starting the server.")
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000, threads=50)
    logging.info("Server is running on port 8000.")

