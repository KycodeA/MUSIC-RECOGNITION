import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"

def test_search_music_endpoint():
    test_audio = "test.mp3"
    assert os.path.exists(test_audio), "File test.mp3 không tồn tại!"

    with open(test_audio, "rb") as f:
        response = client.post(
            "/api/v1/search",
            files={"file": ("test.mp3", f, "audio/mpeg")}
        )

    # In ra nội dung lỗi để debug
    if response.status_code != 200:
        print("\n--- SERVER ERROR DETAIL ---")
        print(response.json())
        print("---------------------------\n")

    assert response.status_code == 200
    json_resp = response.json()
    assert "search_result" in json_resp
    assert "rights_inspection" in json_resp