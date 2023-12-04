from flask import Flask, request
import xmlrpc.client as xmlClient
import sys
import threading
import json
sem = threading.Semaphore()


app = Flask(__name__)
gea = xmlClient.ServerProxy('http://geasouth.cl.gemini.edu/run/ArchiveDataServer.cgi')

@app.route("/archives", methods=['GET'])
def get_archives():
    archives_name_list = []
    archives_key_list = []

    try:
        sem.acquire()
        archives = gea.archiver.archives()
        for arch in archives:
            archives_name_list.append(arch['name'])
            archives_key_list.append(arch['key'])
    except Exception as e:
        print(e)
    finally:
        sem.release() 
        return {"names": archives_name_list, "keys": archives_key_list}


@app.route("/channels", methods=['GET'])
def get_channels():
    try:
        sem.acquire()
        archive_key = request.args.get('archive_key')
        # pattern = request.args.get('pattern')
        channels = gea.archiver.names(int(archive_key),"")
        channels_names = []
        for channel in channels:
            channels_names.append(channel['name'])
    except Exception as e:
        print(e)
    finally:
        sem.release()
        return {"channels":channels_names}

@app.route("/values", methods=['GET'])
def get_values():
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    archive_key = request.args.get('archive')
    channel = request.args.get('channel')
    mode = request.args.get('value_mode')
    n_points = request.args.get('n_points')

    print("archiveKey",archive_key)
    print("mode", mode)
    print("channel",channel)

    try:
        n_points = int(n_points)
        if n_points > 10000:
            n_points = 10000
    except:
        n_points = 3000

    channels_list=[]

    if ',' in channel:
        channel = channel.split(',')
        for chan in channel:
            if(chan not in [" ",""]):
                channels_list.append(chan)
    else:
        channels_list =[channel]

    output={}
    print("chan_list",channels_list)
    if channels_list[0] not in [" ",""]:
        try:
            sem.acquire()
            geaRecord = gea.archiver.values(int(archive_key), channels_list,
                                            int(int(date_from)/1000), 0,
                                            int(int(date_to)/1000), 0,
                                            int(n_points),
                                            int(str(mode)))
        except Exception as e:
            print(e)
        finally:
            sem.release()
            output=geaRecord
    else:
        output=[]
    sys.stdout.flush()

    return {"values":output}

@app.route("/PVselector", methods=['GET'])
def pvSelector():
    f = open('PVselector.json')
    data = json.load(f)
    return(data)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000, threads=50)
