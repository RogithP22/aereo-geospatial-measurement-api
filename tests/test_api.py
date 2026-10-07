import os
import zipfile
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200

def test_invalid_file_extension():
    response = client.post(
        "/api/files/",
        files={"file": ("test.txt", b"some random text", "text/plain")}
    )
    assert response.status_code == 400

def test_corrupted_zip():
    response = client.post(
        "/api/files/",
        files={"file": ("corrupt.zip", b"not a zip file", "application/zip")}
    )
    assert response.status_code == 400

def test_zip_missing_companion_files():
    # Create a zip without .shp, .shx, or .dbf
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.close()
    with zipfile.ZipFile(tmp.name, 'w') as zf:
        zf.writestr("dummy.txt", "hello")
    
    with open(tmp.name, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("incomplete.zip", f, "application/zip")}
        )
    os.unlink(tmp.name)
    assert response.status_code == 400

def test_nonexistent_file_id():
    fake_id = "00000000-0000-0000-0000-000000000000"
    res_get = client.get(f"/api/files/{fake_id}")
    assert res_get.status_code == 404

    res_meas = client.get(f"/api/files/{fake_id}/measurements/")
    assert res_meas.status_code == 404

def test_upload_and_process_sample_kml():
    sample_kml_path = os.path.join("sample_data", "sample.kml")
    if not os.path.exists(sample_kml_path):
        pytest.skip("Sample KML file not found")
    
    with open(sample_kml_path, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["feature_count"] > 0
    
    file_id = data["id"]
    meas_response = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_response.status_code == 200
    meas_data = meas_response.json()
    assert meas_data["total_features"] == data["feature_count"]