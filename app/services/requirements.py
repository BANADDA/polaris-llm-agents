from typing import Dict, Optional

import GPUtil
import psutil

from ..models.schemas import HardwareRequirements


class RequirementsValidator:
    @staticmethod
    def check_hardware_requirements(requirements: HardwareRequirements) -> Dict[str, bool]:
        cpu_cores = psutil.cpu_count()
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        gpus = GPUtil.getGPUs()
        gpu_memory = sum(gpu.memoryTotal for gpu in gpus) / 1024 if gpus else 0
        
        return {
            "cpu": cpu_cores >= requirements.cpu_cores,
            "ram": ram_gb >= requirements.ram_gb,
            "gpu": gpu_memory >= requirements.gpu_memory_gb
        }