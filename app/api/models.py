from typing import Dict, Optional

from pydantic import BaseModel


class DeploymentResponse(BaseModel):
    api_url: str
    container_id: str
    token: Optional[str]

class DeploymentStatus(BaseModel):
    status: str
    error: Optional[str]
    deployment_info: Optional[Dict]