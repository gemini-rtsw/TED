from collections import OrderedDict
from flask import Flask, request, jsonify, Response
import requests
import sys
import json
import yaml
import os
import simplejson as sjson


app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return('Hello from Archiver Appliance service!')

@app.route("/getPvTree", methods=['GET'])
def getPvTree():
    category = request.args.get('category')
    merged_data = {}
    yaml_files = os.listdir(f"./channels/CP/{category}")

    for file_path in yaml_files:
        with open(f"./channels/CP/{category}/{file_path}") as f:
            data = yaml.full_load(f)
            if data:
                merged_data.update(data)

    sorted_merged = OrderedDict(sorted(merged_data.items()))

    return Response(
        json.dumps(sorted_merged, indent=2),
        mimetype='application/json'
    )


@app.route("/getAllPVs", methods=['GET'])
def getAllPVs():
    url = 'http://127.0.0.1:17665/mgmt/bpl/getAllPVs?limit=-1'
    res = requests.get(url)
    return(res.text)

@app.route("/getPVInfo", methods=['GET'])
def getPVInfo(channel, field):
    #channel = request.args.get('channel')
    url = f'http://127.0.0.1:17665/mgmt/bpl/getPVTypeInfo?pv={channel}'
    try:
        res = requests.get(url)
        pvInfoObj = json.loads(res.text)
        res = pvInfoObj[field]
    except Exception as e:
        res = "NONE"
    return(res)


@app.route("/getPVsByPattern", methods=['GET'])
def getPVsByPattern():
    pattern = request.args.get('pattern')
    url = f'http://127.0.0.1:17665/retrieval/bpl/getMatchingPVs?pv={pattern}'
    print("URL:", url)
    try:
        res = requests.get(url)
    except Exception as e:
        res = "NONE"
    resObj = json.loads(res.text)
    return(resObj)

@app.route("/getPV", methods=['GET'])
def getPVs():
    pv = request.args.get('pv')
    print("pv: ",pv)
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    pp_type = request.args.get('pp_type')
    pp_bin = request.args.get('pp_bin')
    chan_list = pv.split(',')
    if len(chan_list)>1:
        pvParam = ''
        for chan in chan_list:
            if(chan!=""):
                url_status = f'http://127.0.0.1:17665/mgmt/bpl/getPVStatus?pv={chan}'
                res_status = requests.get(url_status)
                status = json.loads(res_status.text)
                if "Being archived" in status[0]['status']:
                    pvP = f'pv={pp_type}_{pp_bin}({chan})&'
                    pvParam+=pvP
    else:
        chan = chan_list[0]
        if(chan!=""):
            url_status = f'http://127.0.0.1:17665/mgmt/bpl/getPVStatus?pv={chan}'
            res_status = requests.get(url_status)
            status = json.loads(res_status.text)
            print(status[0]['status'])
            if "Being archived" in status[0]['status']:
                pvParam = f'pv={pp_type}_{pp_bin}({chan_list[0]})&'
    try:
        url = f'http://127.0.0.1:17665/retrieval/data/getDataForPVs.json?{pvParam}from={date_from}&to={date_to}&fetchLatestMetadata=true'
        print("url:", url)
        res = requests.get(url)
        resObj = json.loads(res.text)
        for obj in resObj:
            sys.stdout.flush()
            DBRType = getPVInfo(obj['meta']['name'], "DBRType")
            obj['meta']['dbr_type'] = DBRType

    except:
        resObj={'no data'}
    
    return(sjson.dumps(list(resObj), ignore_nan=True))

@app.route("/getPVDetails", methods=['GET'])
def getPVDetails():
    channel = request.args.get('channel')
    url = f'http://127.0.0.1:17665/mgmt/bpl/getPVDetails?pv={channel}'
    print(url)
    res = requests.get(url)
    return(res.text)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000, threads=50)

