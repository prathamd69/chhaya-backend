import json
import threading
import time

import boto3

from src.core.config import settings
from src.core.logger import configLogger

logger = configLogger(__file__)

# Set by load_data(). The app refuses to start if this is never set.
_snapshot = None


class DataLoadError(RuntimeError):
    """Raised when the cell data cannot be loaded from S3."""


def _install(data, etag):
    """Build a complete new snapshot, then swap it in with one assignment.
    If building raises (e.g. a cell has no 'h3'), the old snapshot is untouched."""
    global _snapshot
    _snapshot = {
        "data": data,
        "body": json.dumps(data).encode("utf-8"),
        "by_h3": {f["properties"]["h3"]: f for f in data["features"]},
        "etag": etag,
        "loaded_at": time.time(),
    }


def _s3_client():
    # Credentials come from the environment, the AWS CLI profile, or the EC2 role
    return boto3.client("s3", region_name=settings.AWS_REGION)


def _load_from_s3():
    logger.info(f"S3 download starting: s3://{settings.S3_BUCKET}/{settings.S3_CELLS_KEY}")
    start = time.perf_counter()

    obj = _s3_client().get_object(Bucket=settings.S3_BUCKET, Key=settings.S3_CELLS_KEY)
    data = json.loads(obj["Body"].read().decode("utf-8"))

    if not data.get("features"):
        raise ValueError("cells file contains no features")

    _install(data, obj["ETag"])

    ms = round((time.perf_counter() - start) * 1000)
    logger.info(f"S3 download succeeded: {len(data['features'])} cells in {ms} ms")


def load_data():
    """Startup load. Raises DataLoadError instead of falling back to mock data."""
    if not settings.S3_BUCKET:
        message = "S3_BUCKET is not set. Add it to your .env file."
        logger.error(message)
        raise DataLoadError(message)

    try:
        _load_from_s3()
    except Exception as e:
        logger.error("S3 load failed", exc_info=True)
        raise DataLoadError(
            f"Could not load s3://{settings.S3_BUCKET}/{settings.S3_CELLS_KEY}: "
            f"{type(e).__name__}: {e}"
        ) from e


def _refresh_loop():
    """Every REFRESH_SECONDS, re-download only if the S3 file changed."""
    while True:
        time.sleep(settings.REFRESH_SECONDS)
        try:
            head = _s3_client().head_object(
                Bucket=settings.S3_BUCKET, Key=settings.S3_CELLS_KEY
            )
            if head["ETag"] != _snapshot["etag"]:
                logger.info("New version detected in S3, reloading")
                _load_from_s3()
            else:
                logger.debug("S3 file unchanged")
        except Exception:
            logger.error("Refresh failed, still serving the last good data", exc_info=True)


def start_background_refresh():
    threading.Thread(target=_refresh_loop, daemon=True).start()
    logger.info(f"Background refresh started (every {settings.REFRESH_SECONDS}s)")


def get_snapshot():
    """Full snapshot: data, pre-serialized body, h3 lookup, etag, timestamp."""
    if _snapshot is None:
        raise DataLoadError("Cell data has not been loaded")
    return _snapshot


def get_cell_data():
    """Parsed GeoJSON (existing routes in cells.py use this unchanged)."""
    return get_snapshot()["data"]