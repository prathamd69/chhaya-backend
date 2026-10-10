import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api import cells
from src.core.config import settings
from src.core.logger import configLogger
from src.services.s3_service import get_snapshot, load_data, start_background_refresh

logger = configLogger(__file__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} (log level {settings.LOG_LEVEL})")
    load_data()
    start_background_refresh()
    cell_count = len(get_snapshot()["data"]["features"])
    logger.info(f"Startup complete: {cell_count} cells loaded from S3")
    yield
    logger.info("Shutting down")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Delhi Climate Planning Engine",
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
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
    ms = round((time.perf_counter() - start) * 1000)
    level = logging.DEBUG if request.url.path == "/health" else logging.INFO
    logger.log(level, f"{request.method} {request.url.path} -> {response.status_code} ({ms} ms)")
    return response

@app.get("/health")
def health_check():
    snap = get_snapshot()
    return {
        "status": "ok",
        "cell_count": len(snap["data"]["features"]),
        "loaded_at": snap["loaded_at"],
        "etag": snap["etag"],
    }

app.include_router(cells.router)