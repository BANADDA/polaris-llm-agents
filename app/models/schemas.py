from pydantic import BaseModel

class HardwareRequirements(BaseModel):
    cpu_cores: int
    ram_gb: int
    storage_gb: float
    gpu_memory_gb: int

class ModelSpecs(BaseModel):
    parameters: str
    context_size: int
    precision: str

class DeploymentRequest(BaseModel):
    model_id: str
    api_name: str
    user_id: str
    ssh_config: dict