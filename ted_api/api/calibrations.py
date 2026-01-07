import json
import asyncio

from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import StreamingResponse
from fastapi import APIRouter,Request,Response

from calibrations.calibrations import getDirsByPrefix,insertDay, queryCalib

router = APIRouter(
    prefix="/calibrations",
    tags=["calibrations"],
)

calib_executor = ThreadPoolExecutor(max_workers=2)
@router.get("/load/{prefix}")
async def load_prefix(prefix: str):
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

@router.get("/query")
async def get_data(request: Request):
    date =  request.query_params.get("date")
    key =  request.query_params.get("key")
    data = queryCalib(date,key)
    json_ready = [
        {
            "time": row[0].isoformat(),
            "key": row[1],
            "value": row[2]
        }
        for row in data
    ]
    json_str = json.dumps(json_ready)
    return Response(json_str)