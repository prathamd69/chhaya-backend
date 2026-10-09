from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import cells
from src.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Delhi Climate Planning Engine"
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