import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import calibrations, pv_tree, archappl
def create_app() -> FastAPI:
    app = FastAPI(
        title="TED API",
        version="1.0.0"
    ) 

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            os.getenv("GRAFANA_TED_URL"),
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(calibrations.router)
    app.include_router(pv_tree.router)
    app.include_router(archappl.router)

    return app
app = create_app()