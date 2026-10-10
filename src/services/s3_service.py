import json
import threading
import time
from pathlib import Path

import boto3

from src.core.logger import configLogger
from src.core.config import Settings

logger = configLogger(__file__)

MOCK_PATH = Path("contract/mock_cells.geojson")

# One immutable snapshot, replaced as a whole. Readers never see a partial update.
_snapshot = {
    "data": {"type": "FeatureCollection", "features": []},
    "body": b'{"type":"FeatureCollection","features":[]}',
    "by_h3": {},
    "etag": None,
    "source": "none",
    "loaded_at": None,
}

def _install(data, etag, source):
    """Build a new snapshot and swap it in with a single assignment."""
    global _snapshot
    _snapshot = {
        "data": data,
        "body": json.dumps(data).encode("utf-8"),
        "by_h3": {f["properties"]["h3"]: f for f in data["features"]},
        "etag": etag,
        "source": source,
        "loaded_at": time.time(),
    }


def _s3_configured():
    return bool(Settings.S3_BUCKET) and Settings.S3_BUCKET != "your-bucket-name-here"


def _s3_client():
    # No keys passed: boto3 uses the EC2 IAM role automatically
    return boto3.client("s3", region_name=Settings.AWS_REGION)


def _load_from_s3():
    logger.info(
        "S3 download starting",
        extra={"bucket": Settings.S3_BUCKET, "key": Settings.S3_CELLS_KEY},
    )
    start = time.perf_counter()
    obj = _s3_client().get_object(Bucket=Settings.S3_BUCKET, Key=Settings.S3_CELLS_KEY)
    data = json.loads(obj["Body"].read().decode("utf-8"))
    _install(data, obj["ETag"], "s3")
    logger.info(
        "S3 download succeeded",
        extra={
            "bucket": Settings.S3_BUCKET,
            "key": Settings.S3_CELLS_KEY,
            "cells": len(data["features"]),
            "duration_ms": round((time.perf_counter() - start) * 1000),
        },
    )


def _load_mock():
    logger.warning("Falling back to MOCK data", extra={"path": str(MOCK_PATH)})
    if MOCK_PATH.exists():
        with open(MOCK_PATH, "r") as f:
            _install(json.load(f), None, "mock")
    else:
        logger.error("Mock data file not found, serving empty data")


def load_data():
    """Startup load: try S3 first, fall back to mock."""
    if _s3_configured():
        try:
            _load_from_s3()
            return
        except Exception:
            logger.error("S3 load failed", exc_info=True)
    else:
        logger.warning("S3_BUCKET not configured, skipping S3")
    _load_mock()


def _refresh_loop():
    """Every REFRESH_SECONDS, re-download only if the S3 file changed."""
    while True:
        time.sleep(Settings.REFRESH_SECONDS)
        if not _s3_configured():
            continue
        try:
            head = _s3_client().head_object(
                Bucket=Settings.S3_BUCKET, Key=Settings.S3_CELLS_KEY
            )
            if head["ETag"] != _snapshot["etag"]:
                logger.info("New version detected in S3, reloading")
                _load_from_s3()
            else:
                logger.debug("S3 file unchanged")
        except Exception as e:
            logger.warning("Refresh failed, keeping current data", extra={"error": str(e)})


def start_background_refresh():
    threading.Thread(target=_refresh_loop, daemon=True).start()
    logger.info("Background refresh started", extra={"interval_s": Settings.REFRESH_SECONDS})


def get_cell_data():
    """Parsed GeoJSON (kept so existing routes work unchanged)."""
    return _snapshot["data"]


def get_snapshot():
    """Full snapshot: data, pre-serialized body, h3 lookup, source, timestamps."""
    return _snapshot