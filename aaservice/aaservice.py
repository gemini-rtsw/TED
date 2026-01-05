# Standard library imports
import json
import os
import time
from collections import OrderedDict
from datetime import datetime

# Third-party imports
import httpx
import yaml
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request, Response, HTTPException, Body
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse, StreamingResponse

import asyncio

# Local application imports
from enum_loader import loadAllEnumsAtOnce
from ted_calibrations import getDirsByPrefix, insertDay

app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://ted-dev.cl.gemini.edu",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/getPvTree")
async def get_pv_tree(request: Request):
    category =  request.query_params.get("category")
    merged_data = {}
    yaml_files = os.listdir(f"./channels/CP/{category}")
    for file_path in yaml_files:
        with open(f"./channels/CP/{category}/{file_path}") as f:
            data = yaml.full_load(f)
            if data:
                merged_data.update(data)
    sorted_merged = OrderedDict(sorted(merged_data.items()))
    return Response(json.dumps(sorted_merged, indent=2))

@app.get("/getSystemTree")
async def get_system_tree(request: Request):
    category =  request.query_params.get("category")
    system =  request.query_params.get("system").lower()
    with open(f"./channels/CP/{category}/{system}.yaml") as f:
        data = yaml.full_load(f)
    sorted_merged = OrderedDict(sorted(data.items()))
    return Response(json.dumps(sorted_merged, indent=2))


@app.get("/getSystemsByCategory")
async def get_system_by_category(request: Request):
    category = request.query_params.get("category")
    yaml_files = os.listdir(f"./channels/CP/{category}")
    systems=[]
    for file in yaml_files:
        systems.append(file.split(".")[0].upper())
    return Response(json.dumps(systems, indent=2))


def get_bin_size(delta_seconds: float) -> int:
    h = delta_seconds / 3600
    if h < 1:
        return -1 # Less than a hour: RAW data
    if h < 6:
        return 1 # Less than 6 hours: bins of 1 second
    elif h < 24:
        return 5 # Less than a day: bins of 5 second
    elif h < 24 * 7:
        return 60 # Less than a week: bins of 1 minute
    elif h < 24 * 30:
        return 300 # Less than a month: bins of 5 minutes
    else:
        return 3600 # Less than a year: bins of 1 hour
#===================================================================================================

GET_DATA_URL = "http://127.0.0.1:17665/retrieval/data/getDataForPVs.json"
GET_PV_TYPE_URL = "http://127.0.0.1:17665/mgmt/bpl/getPVTypeInfo"
GET_ALL_PVS_URL = "http://127.0.0.1:17665/mgmt/bpl/getAllPVs?limit=-1"

@app.get("/getAllPVs")
async def get_all_pvs_url():
    async with httpx.AsyncClient() as client:
        response = await client.get(GET_ALL_PVS_URL)
        data = response.json() 
    return data

@app.get("/getPVs")
async def get_pvs(request: Request):
    #Obtain request
    date_from = request.query_params.get("from", "")
    date_to = request.query_params.get("to", "")
    pv_names = request.query_params.get("pv", "").split(",")
    pp_mode = request.query_params.get("pp_mode", "")
    pp_bin = request.query_params.get("pp_bin", "")

    #This is for adapting the params to the archiver appliance query
    query_params = []
    
    #Obtain bin size depending on the deltatime
    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    deltaDate = datetime.strptime(date_to, fmt) - datetime.strptime(date_from, fmt)
    delta_seconds = deltaDate.total_seconds()

    delta_days = deltaDate.total_seconds()/(3600*24)
    print("DELTA DAYS: ",delta_days)
    if (delta_days>30):
        return {"errorMsg":"Query limited to < 30 days"}

    bin_size = get_bin_size(delta_seconds)

    #Store PV type info per PV
    pv_metadata = {}
    
    async with httpx.AsyncClient() as client:
        for pv_name in pv_names:
            if not pv_name:
                continue
            # Fetch PV type info
            response = await client.get(f"{GET_PV_TYPE_URL}?pv={pv_name}")
            pv_type_info = response.json()
            pv_type = pv_type_info["DBRType"]

            enum_strs = None
            if pv_type == "DBR_SCALAR_ENUM":
                enum_strs = pv_type_info["extraFields"]["enum_strs"]

            # Initialize defaults for this PV
            effective_pp_bin = pp_bin
            effective_pp_mode = pp_mode

            if effective_pp_bin == "auto":
                effective_pp_bin = bin_size
                if effective_pp_bin == -1:
                    effective_pp_mode = "raw"

            if pv_type in ("DBR_SCALAR_ENUM", "DBR_SCALAR_STRING"):
                effective_pp_mode = "firstFill"
                effective_pp_bin = 1

            query_params.append(("pv", f"{effective_pp_mode}_{effective_pp_bin}({pv_name})"))


        # Store PV type info for later
        pv_metadata[pv_name] = {
            "pv_type": pv_type,
            "enum_strs": enum_strs,
        }

        print("=================================================")
        print(f"pv_name: {pv_name}")
        print(f"pv_type: {pv_type}")
        print(f"date_from: {date_from}")
        print(f"date_to: {date_to}")
        print(f"deltaDate: {deltaDate}")
        print(f"pp_bin: {effective_pp_bin}")
        print(f"pp_mode: {effective_pp_mode}")
        print("=================================================")


    # Pass through other query params
    for k, v in request.query_params.multi_items():
        if k not in ("pv", "pp_mode", "pp_bin"):
            query_params.append((k, v))

    # Query Archiver Appliance
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.get(GET_DATA_URL, params=query_params)
        print(query_params)
        r.raise_for_status()
        data = r.json()

    # Data adjustments
    for channel in data:
        pv_name = channel["meta"]["name"]
        pv_info = pv_metadata.get(pv_name, {})

        pv_type = pv_info.get("pv_type")
        enum_strs = pv_info.get("enum_strs")

        channel["meta"]["type"] = pv_type

        # Apply enum/string transformation per PV
        if pv_type == "DBR_SCALAR_ENUM" and enum_strs:
            enumList = json.loads(enum_strs)
            for point in channel.get("data", []):
                val = point.get("val")
                if isinstance(val, int) and 0 <= val < len(enumList):
                    point["val"] = enumList[val]
                else:
                    point["val"] = None
        # This is a workaround to a weird Archiver Appliance issue, the first values sometimes is messsed up. 
        if pv_type == "DBR_SCALAR_DOUBLE":
            if "data" in channel and channel["data"]:
                channel["data"].pop(0)
    return data

#===================================================================================================

@app.get("/loadEnums")
async def loadAllEnums(request: Request):
    enums = await loadAllEnumsAtOnce()
    return {"updated_pvs": enums}

#===================================================================================================
calib_executor = ThreadPoolExecutor(max_workers=2)
@app.get("/loadCalibrations/{prefix}")
async def loadPrefixCalib(prefix: str):

    async def event_generator():
        try:
            days = list(getDirsByPrefix(prefix))
            total = len(days)

            for i, day in enumerate(days, start=1):
                yield f"data: [{i}/{total}] Loading {day}...\n\n"
                await asyncio.get_running_loop().run_in_executor(
                    calib_executor, insertDay, day
                )

            yield "data: DONE\n\n"
        except Exception as e:
            yield f"data: ERROR: {e}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
