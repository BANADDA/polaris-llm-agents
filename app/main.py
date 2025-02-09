from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import endpoints
from .config.firebase import init_firebase

app = FastAPI(title="Model Deployment Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase
init_firebase()

# Include routers
app.include_router(endpoints.router, prefix="/api/v1")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}