import logging

from fastapi import FastAPI

from app.api import router_api
from app.config import settings

logging.basicConfig(level=settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(router_api)
