from fastapi import APIRouter, HTTPException

from src.core.logger import configLogger
from src.services.s3_service import get_cell_data

logger = configLogger(__file__)

router = APIRouter()


@router.get("/cells")
def get_cells():
    """
    Returns the full GeoJSON FeatureCollection.
    Data is served instantly from memory (loaded on startup from S3).
    """
    return get_cell_data()


@router.get("/cells/{h3}")
def get_cell_by_h3(h3: str):
    """
    Returns a single cell by its H3 index.
    """
    data = get_cell_data()
    for feature in data.get("features", []):
        if feature.get("properties", {}).get("h3") == h3:
            return feature

    logger.warning(f"Cell not found: {h3}")
    raise HTTPException(status_code=404, detail=f"Cell with H3 {h3} not found")


@router.get("/wards")
def get_ward_summaries():
    """
    Returns aggregated summaries (population, average priority) for each ward.
    """
    data = get_cell_data()
    wards = {}

    for feature in data.get("features", []):
        props = feature.get("properties", {})
        ward_name = props.get("ward", "Unknown")

        if ward_name not in wards:
            wards[ward_name] = {
                "ward": ward_name,
                "cell_count": 0,
                "total_population": 0,
                "avg_priority": 0.0,
                "_priority_sum": 0.0,
            }

        wards[ward_name]["cell_count"] += 1
        wards[ward_name]["total_population"] += props.get("population", 0)
        wards[ward_name]["_priority_sum"] += props.get("priority", 0.0)

    # Calculate final averages and clean up
    result = []
    for w_data in wards.values():
        if w_data["cell_count"] > 0:
            w_data["avg_priority"] = round(w_data["_priority_sum"] / w_data["cell_count"], 4)
        del w_data["_priority_sum"]
        result.append(w_data)

    return result