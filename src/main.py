from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import cells
from src.core.config import settings
from src.services.s3_service import load_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data from S3 (or fallback to mock) when server boots
    load_data()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Delhi Climate Planning Engine",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

app.include_router(cells.router)