from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, logger

from ..models.schemas import DeploymentRequest
from ..services.deployment import DeploymentService
from ..services.model_registry import ModelRegistry

router = APIRouter()
deployment_service = DeploymentService()
model_registry = ModelRegistry()

@router.post("/deploy")
async def deploy_model(payload: dict):
    try:
        deployment_service = DeploymentService()
        result = await deployment_service.deploy_model(
            model_id=payload["model_id"],
            user_id=payload["user_id"],
            api_name=payload["api_name"],
            ssh_config=payload["ssh_config"]
        )
        return result
    except Exception as e:
        # Instead of letting the exception propagate causing a 500 error
        # Log the error and return an appropriate response
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# @router.post("/deploy")
# async def deploy_model(request: DeploymentRequest) -> Dict:
#     try:
#         result = await deployment_service.deploy_model(
#             request.model_id,
#             request.user_id,
#             request.api_name,
#             request.ssh_config
#         )
        
#         # Format response with all endpoints
#         port = result["api_url"].split(":")[-1]
#         base_url = f"http://{request.ssh_config['host']}:{port}"
        
#         return {
#             "status": "success",
#             "deployment": {
#                 "model_id": request.model_id,
#                 "container_id": result["container_id"],
#                 "endpoints": {
#                     "base_url": base_url,
#                     "token": f"{base_url}/token",
#                     "inference": f"{base_url}/inference"
#                 },
#                 "usage": {
#                     "token_request": {
#                         "method": "POST",
#                         "params": {
#                             "user_id": request.user_id,
#                             "model_id": request.model_id
#                         }
#                     },
#                     "inference_request": {
#                         "method": "POST",
#                         "headers": {
#                             "X-API-Key": "<token from /token endpoint>"
#                         }
#                     }
#                 }
#             }
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-requirements/{model_id}")
async def validate_requirements(model_id: str) -> Dict:
    requirements = await model_registry.get_model_requirements(model_id)
    if not requirements:
        raise HTTPException(status_code=404)
    return requirements.dict()

@router.get("/deployments/{user_id}")
async def get_user_deployments(user_id: str) -> Dict:
    deployments = await model_registry.get_user_deployments(user_id)
    return {"deployments": deployments}