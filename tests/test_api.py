from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_deploy_request_print():
    payload = {
        "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        "user_id": "test-user",
        "api_name": "polaris-deepseek-7B-banadda",
        "ssh_config": {
            "host": "24.83.13.62",
            "username": "tang",
            "port": "15000",
            "password": "Yogptcommune1"
        }
    }
    
    response = client.post("/api/v1/deploy", json=payload)
    data = response.json()
    

    print("\n=== Deployment Response ===")
    print(data)
    

    assert response.status_code == 200
