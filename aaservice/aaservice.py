from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import os
import yaml
import json
from collections import OrderedDict
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/getAllPVs")
async def getAllPVs():
    url = "http://127.0.0.1:17665/mgmt/bpl/getAllPVs?limit=-1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json() 
    return data

@app.get("/getPvTree")
async def getPvTree(request: Request):
    category =  request.query_params.get("category")
    merged_data = {}
    yaml_files = os.listdir(f"./channels/CP/{category}")
    for file_path in yaml_files:
        with open(f"./channels/CP/{category}/{file_path}") as f:
            data = yaml.full_load(f)
            if data:
                merged_data.update(data)
    sorted_merged = OrderedDict(sorted(merged_data.items()))
    return Response(
    json.dumps(sorted_merged, indent=2)
    )

archiver_url = "http://127.0.0.1:17665/retrieval/data/getDataForPVs.json"

@app.get("/getPV")
async def getPV(request: Request):
    # Extract parameters
    pv_values = request.query_params.get("pv", "").split(",")
    pp_type = request.query_params.get("pp_type", "")
    pp_bin = request.query_params.get("pp_bin", "")

    # Rebuild query params:
    # transform each pv into "pv={pp_type}_{pp_bin}({pv})"
    query_params = []
    for pv in pv_values:
        pv = pv.strip()
        if pv:
            query_params.append(("pv", f"{pp_type}_{pp_bin}({pv})"))
    for k, v in request.query_params.multi_items():
        if k not in ("pv", "pp_type", "pp_bin"):
            query_params.append((k, v))

    async def stream_archiver():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "GET", archiver_url, params=query_params, headers={"Accept-Encoding": "gzip"}
            ) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk

    return StreamingResponse(stream_archiver(), media_type="application/json")

