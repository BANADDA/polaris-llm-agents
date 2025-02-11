import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from ..models.schemas import DeploymentRequest
from ..services.deployment import DeploymentService
from ..services.model_registry import ModelRegistry

router = APIRouter()
deployment_service = DeploymentService()
model_registry = ModelRegistry()
logger = logging.getLogger(__name__)

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
        logger.error(f"Deployment failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/validate-requirements/{model_id}")
async def validate_requirements(model_id: str) -> Dict:
    requirements = await model_registry.get_model_requirements(model_id)
    if not requirements:
        raise HTTPException(status_code=404, detail="Model requirements not found")
    return requirements.dict()

@router.get("/deployments/{user_id}")
async def get_user_deployments(user_id: str) -> Dict:
    deployments = await model_registry.get_user_deployments(user_id)
    return {"deployments": deployments}
