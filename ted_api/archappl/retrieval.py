
import json
import httpx
from datetime import datetime

GET_DATA_URL = "http://127.0.0.1:17665/retrieval/data/getDataForPVs.json"
GET_PV_TYPE_URL = "http://127.0.0.1:17665/mgmt/bpl/getPVTypeInfo"
GET_ALL_PVS_URL = "http://127.0.0.1:17665/mgmt/bpl/getAllPVs?limit=-1"

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

async def get_all_channels():
    async with httpx.AsyncClient() as client:
        response = await client.get(GET_ALL_PVS_URL)
        data = response.json() 
    return data

async def fetch_channels(request):
     # ---- Parse params ----
    date_from = request.query_params.get("from", "")
    date_to = request.query_params.get("to", "")
    pv_names = request.query_params.get("pv", "").split(",")
    pp_mode = request.query_params.get("pp_mode", "")
    pp_bin = request.query_params.get("pp_bin", "")

    fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
    delta = datetime.strptime(date_to, fmt) - datetime.strptime(date_from, fmt)

    delta_days = delta.total_seconds() / 86400
    if delta_days > 30:
        raise ValueError("Query limited to < 30 days")

    bin_size = get_bin_size(delta.total_seconds())

    query_params = []
    pv_metadata = {}

    # ---- Fetch PV metadata ----
    async with httpx.AsyncClient() as client:
        for pv_name in pv_names:
            if not pv_name:
                continue

            r = await client.get(f"{GET_PV_TYPE_URL}?pv={pv_name}")
            info = r.json()

            pv_type = info["DBRType"]
            enum_strs = None

            if pv_type == "DBR_SCALAR_ENUM":
                enum_strs = info["extraFields"]["enum_strs"]

            effective_pp_mode = pp_mode
            effective_pp_bin = pp_bin

            if effective_pp_bin == "auto":
                effective_pp_bin = bin_size
                if effective_pp_bin == -1:
                    effective_pp_mode = "raw"

            if pv_type in ("DBR_SCALAR_ENUM", "DBR_SCALAR_STRING"):
                effective_pp_mode = "firstFill"
                effective_pp_bin = 1

            query_params.append(
                ("pv", f"{effective_pp_mode}_{effective_pp_bin}({pv_name})")
            )

            pv_metadata[pv_name] = {
                "pv_type": pv_type,
                "enum_strs": enum_strs,
            }

    # ---- Pass-through other params ----
    for k, v in request.query_params.multi_items():
        if k not in ("pv", "pp_mode", "pp_bin"):
            query_params.append((k, v))

    # ---- Query Archiver ----
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.get(GET_DATA_URL, params=query_params)
        r.raise_for_status()
        data = r.json()

    # ---- Post-process data ----
    for channel in data:
        pv_name = channel["meta"]["name"]
        meta = pv_metadata.get(pv_name, {})

        pv_type = meta.get("pv_type")
        enum_strs = meta.get("enum_strs")

        channel["meta"]["type"] = pv_type

        if pv_type == "DBR_SCALAR_ENUM" and enum_strs:
            enum_list = json.loads(enum_strs)
            for point in channel.get("data", []):
                val = point.get("val")
                point["val"] = (
                    enum_list[val] if isinstance(val, int) and val < len(enum_list)
                    else None
                )

        # Archiver workaround
        if pv_type == "DBR_SCALAR_DOUBLE":
            if channel.get("data"):
                channel["data"].pop(0)
    return data
