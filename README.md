# Model Deployment Service

Service for deploying ML models with authentication and remote execution capabilities.

## Features
- Model templates for text, speech, and image models
- Custom deployment per user
- Token-based authentication
- Remote machine deployment via SSH
- GPU requirement validation
- Firebase integration for model registry

## Prerequisites
- Python 3.8+
- Docker
- GPU support
- Firebase credentials

## Setup
```bash
python -m venv deploy_venv
source deploy_venv/bin/activate  # Windows: deploy_venv\Scripts\activate
pip install -r requirements.txt
Configuration

Add Firebase credentials to app/config/firebase.json
Update model templates as needed
Register models using model_registry.py

Usage
bashCopy uvicorn app.main:app --reload

## Register Models
```bash
python model_registry.py
```

## Run Service 
```bash
uvicorn app.main:app --reload --port 8000
```

## API Usage

```bash
Endpoints:

POST /api/v1/deploy - Deploy model
POST /api/v1/validate-requirements/{model_id} - Validate hardware
GET /api/v1/deployments/{user_id} - List deployments
```

### Deploy Model
```bash
curl -X POST http://localhost:8000/api/v1/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "openai/whisper-large-v3",
    "api_name": "my-whisper-api",
    "user_id": "user123",
    "ssh_config": {
      "host": "remote-machine.com",
      "username": "user",
      "password": "pass"
    }
  }'
```

### Get Token
```bash
curl -X POST http://localhost:8000/api/v1/token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "model_id": "openai/whisper-large-v3"
  }'
```

### Make Inference
```bash
curl -X POST http://your-api-url/inference \
  -H "X-API-Key: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your input here"
  }'
```

## Example Deployment Flow
1. Register models
2. Deploy model
3. Get auth token
4. Use token for inference

## Requirements
- Python 3.8+
- Docker
- GPU support
- Firebase credentials
```