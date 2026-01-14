from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from pv_tree.pv_tree import get_tree

import httpx


from archappl.enum_loader import load_all_enums
from archappl.retrieval import get_all_channels, fetch_channels

router = APIRouter(
    prefix="/archappl",
    tags=["archappl"],
)

@router.get("/load-enums")
async def load_all_enums_ep(request: Request):
    enums = await load_all_enums()
    return {"updated_pvs": enums}

@router.get("/get-all-channels")
async def get_all_channels_ep():
    data = await get_all_channels()
    return JSONResponse(data)

@router.get("/get-values")
async def get_values(request: Request):
    try:
        return await fetch_channels(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))