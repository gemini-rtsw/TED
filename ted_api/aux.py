
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