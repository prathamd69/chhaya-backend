import pytest
from fastapi.testclient import TestClient

from src.core.config import settings
from src.main import app
from src.services.s3_service import DataLoadError, load_data

REQUIRED = ["h3", "ndvi", "population", "built_frac", "dust_idx", "school_count", "ward", "priority"]


@pytest.fixture(scope="module")
def client():
    # Using "with" runs the app's startup, which loads the data from S3
    with TestClient(app) as c:
        yield c


def test_health_reports_loaded_data(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["cell_count"] > 0
    assert body["etag"]


def test_cells_is_a_feature_collection(client):
    data = client.get("/cells").json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0


def test_every_cell_has_all_contract_fields(client):
    features = client.get("/cells").json()["features"]
    for f in features:
        for key in REQUIRED:
            assert key in f["properties"], f"cell {f['properties'].get('h3')} is missing {key}"


def test_single_cell_lookup(client):
    first = client.get("/cells").json()["features"][0]
    h3 = first["properties"]["h3"]
    response = client.get(f"/cells/{h3}")
    assert response.status_code == 200
    assert response.json()["properties"]["h3"] == h3


def test_unknown_cell_returns_404(client):
    assert client.get("/cells/does-not-exist").status_code == 404


def test_ward_totals_match_the_cells(client):
    features = client.get("/cells").json()["features"]
    wards = client.get("/wards").json()
    assert sum(w["cell_count"] for w in wards) == len(features)
    expected_population = sum(f["properties"]["population"] for f in features)
    assert sum(w["total_population"] for w in wards) == pytest.approx(expected_population)


def test_cors_header_is_present(client):
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" in response.headers


def test_empty_bucket_raises(monkeypatch):
    monkeypatch.setattr(settings, "S3_BUCKET", "")
    with pytest.raises(DataLoadError):
        load_data()


def test_nonexistent_bucket_raises(monkeypatch):
    monkeypatch.setattr(settings, "S3_BUCKET", "chhaya-bucket-that-does-not-exist-123")
    with pytest.raises(DataLoadError):
        load_data()