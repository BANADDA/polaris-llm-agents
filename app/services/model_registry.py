from typing import Dict, Optional

from firebase_admin import firestore

from ..config.firebase import db
from ..models.schemas import HardwareRequirements, ModelSpecs


class ModelRegistry:
    def __init__(self):
        self.model_collection = db.collection('models')
        
    async def get_model_details(self, model_id: str) -> Optional[Dict]:
        # Sanitize model_id by replacing "/" with "-" so it becomes a valid document ID.
        safe_model_id = model_id.replace("/", "-")
        
        # First, try to get the document by its sanitized ID
        doc = self.model_collection.document(safe_model_id).get()
        if doc.exists:
            return doc.to_dict()
        
        # If not found, try to query by the "name" field using the original model_id.
        query = self.model_collection.where("name", "==", model_id).limit(1).stream()
        for d in query:
            return d.to_dict()
        
        return None
        
    async def get_model_requirements(self, model_id: str) -> Optional[HardwareRequirements]:
        doc = await self.get_model_details(model_id)
        if doc and 'requirements' in doc:
            return HardwareRequirements(**doc['requirements'])
        return None
        
    async def get_model_specs(self, model_id: str) -> Optional[ModelSpecs]:
        doc = await self.get_model_details(model_id)
        if doc and 'specifications' in doc:
            return ModelSpecs(**doc['specifications'])
        return None
        
    async def get_model_type(self, model_id: str) -> Optional[str]:
        doc = await self.get_model_details(model_id)
        # Return the model_type if present
        return doc.get('model_type') if doc else None
