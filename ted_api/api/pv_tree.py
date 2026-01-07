from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from pv_tree.pv_tree import get_tree
router = APIRouter(
    prefix="/channels-tree",
    tags=["channels-tree"],
)

@router.get("/get")
async def get_tree_ep(category: str = Query(..., description="Category name")):
    print(category)
    res = get_tree(category)
    return JSONResponse(res)

# @router.get("/get-by-system")
# async def get_system_tree_ep(request: Request):
#     category =  request.query_params.get("category")
#     system =  request.query_params.get("system").lower()
#     get_system_tree(categroy, system)
#     return Response(res)


# @router.get("/get-by-category")
# async def get_category_tree_ep(request: Request):
#     category = request.query_params.get("category")
#     res = get_category_tree(category)
#     return Response(res)
