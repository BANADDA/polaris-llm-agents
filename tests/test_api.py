from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_deploy_request_print():
    payload = {
        "model_id": "apple/OpenELM-270M",
        "user_id": "test-user",
        "api_name": "pola-open-elm",
        "ssh_config": {
            "host": "24.83.13.62",
            "username": "tang",
            "port": "11000",
            "password": "Yogptcommune1"
        }
    }
    
    response = client.post("/api/v1/deploy", json=payload)
    data = response.json()
    

    print("\n=== Deployment Response ===")
    print(data)
    

    assert response.status_code == 200
