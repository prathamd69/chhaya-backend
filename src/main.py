import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api import cells
from src.core.config import Settings
from src.core.logger import configLogger
from src.services.s3_service import get_snapshot, load_data, start_background_refresh

logger = configLogger(__file__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data from S3 (or fallback to mock) when server boots
    logger.info(
        "Starting application",
        extra={
            "project": Settings.PROJECT_NAME,
            "log_level": Settings.LOG_LEVEL,
            "bucket": Settings.S3_BUCKET,
        },
    )
    load_data()
    start_background_refresh()
    snap = get_snapshot()
    logger.info(
        "Startup complete",
        extra={"data_source": snap["source"], "cells": len(snap["data"]["features"])},
    )
    yield
    logger.info("Shutting down")

app = FastAPI(
    title=Settings.PROJECT_NAME,
    description="Backend API for Delhi Climate Planning Engine",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

origins = [o.strip() for o in Settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    level = logging.DEBUG if request.url.path == "/health" else logging.INFO
    logger.log(
        level,
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.perf_counter() - start) * 1000),
        },
    )
    return response

@app.get("/health")
def health_check():
    snap = get_snapshot()
    return {
        "status": "ok",
        "data_source": snap["source"],
        "cell_count": len(snap["data"]["features"]),
        "loaded_at": snap["loaded_at"],
    }

app.include_router(cells.router)