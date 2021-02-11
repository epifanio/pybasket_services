import asyncio
import json
from pathlib import Path

import fastapi
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from api import nc_api
from views import home, dashboard, download

app = fastapi.FastAPI(title="PyBasket",
                      description="Prototype API for METSIS Basket app",
                      version="0.0.1",
                      )

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_PROCESSING_SECOND = 600


def configure():
    configure_routing()
    # configure_api_keys()
    # configure_fake_data()


def configure_routing():
    app.mount('/static', StaticFiles(directory='/app/static'), name='static')
    app.mount('/download', StaticFiles(directory='/app/download'), name='download')
    app.include_router(nc_api.router)
    app.include_router(home.router)
    app.include_router(dashboard.router)
    app.include_router(download.router)


if __name__ == '__main__':
    configure()
    uvicorn.run(app, port=9000, host='10.0.0.100')
else:
    configure()
