from flask import Flask, request
import xmlrpc.client as xmlClient
import sys
import threading
import json

sem = threading.Semaphore()

app = Flask(__name__)
gea = xmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')

@app.route("/archives", methods=['GET'])
def getArchives():
    archivesNameList = []
    archivesKeyList = []

    try:
        sem.acquire()
        archives = gea.archiver.archives()
        for arch in archives:
            archivesNameList.append(arch['name'])
            archivesKeyList.append(arch['key'])
    except Exception as e:
        print(e)
    finally:
        sem.release()
        return {"names": archivesNameList, "keys": archivesKeyList}

@app.route("/channels", methods=['GET'])
def getChannels():
    try:
        sem.acquire()
        archiveKey = request.args.get('archive_key')
        channels = gea.archiver.names(int(archiveKey), "")
        channelsNames = ['None']
        for channel in channels:
            channelsNames.append(channel['name'])
    except Exception as e:
        print(e)
    finally:
        with open('channels.json', 'w') as jsonFile:
            json.dump({"channels": channelsNames}, jsonFile, indent=4)
        sem.release()
        return {"channels": channelsNames}

@app.route("/values", methods=['GET'])
def getValues():
    dateFrom = request.args.get('from')
    dateTo = request.args.get('to')
    archiveKey = request.args.get('archive')
    channel = request.args.get('channel')
    mode = request.args.get('value_mode')
    nPoints = request.args.get('n_points')

    try:
        nPoints = int(nPoints)
        if nPoints > 10000:
            nPoints = 10000
    except ValueError:
        nPoints = 3000

    channelsList = []

    if ',' in channel:
        channelsList = [chan.strip() for chan in channel.split(',') if chan.strip() and chan not in ["", " ", "None"]]
    else:
        if channel.strip() and channel not in ["", " ", "None"]:
            channelsList = [channel.strip()]

    output = {}
    if channelsList:
        try:
            sem.acquire()
            geaRecord = gea.archiver.values(
                int(archiveKey), channelsList,
                int(int(dateFrom) / 1000), 0,
                int(int(dateTo) / 1000), 0,
                int(nPoints),
                int(mode)
            )
        except Exception as e:
            print(e)
        finally:
            sem.release()
            output = geaRecord
    else:
        output = []

    sys.stdout.flush()
    return {"values": output}

@app.route("/pvSelector", methods=['GET'])
def pvSelector():
    with open('PVselector.json') as file:
        data = json.load(file)
    return data

@app.route("/allSubsystems", methods=['GET'])
def allSubsystems():
    with open('allSubsystems.json') as file:
        dataSubs = json.load(file)
    return dataSubs

@app.route("/allChannels", methods=['GET'])
def allChannels():
    with open('channels.json') as file:
        dataChannels = json.load(file)
    return dataChannels

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000, threads=50)

