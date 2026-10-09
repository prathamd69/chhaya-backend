import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

MOCK_FILE_PATH = Path("contract/mock_cells.geojson")

@router.get("/cells")
def get_cells():
    """
    Serves the mock GeoJSON file for the frontend to build against tonight.
    Later, this will load the real cells.geojson from S3[cite: 4].
    """
    if not MOCK_FILE_PATH.exists():
        raise HTTPException(status_code=404, detail="Mock data file not found.")
    
    with open(MOCK_FILE_PATH, "r") as f:
        data = json.load(f)
        
    return data