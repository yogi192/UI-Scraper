from fastapi import APIRouter, HTTPException, Depends
from app.config import settings as app_settings
from pydantic import BaseModel
import os

router = APIRouter()

class UpdateSettingsRequest(BaseModel):
    google_api_key: str

class SettingsResponse(BaseModel):
    has_google_api_key: bool

@router.get("/", response_model=SettingsResponse)
async def get_settings():
    return {
        "has_google_api_key": bool(app_settings.google_api_key or app_settings.api_key)
    }

@router.put("/")
async def update_settings(request: UpdateSettingsRequest):
    # Update environment variable
    os.environ["API_KEY"] = request.google_api_key
    os.environ["GOOGLE_API_KEY"] = request.google_api_key
    
    # Update settings
    app_settings.google_api_key = request.google_api_key
    app_settings.api_key = request.google_api_key
    
    # Optionally save to .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    with open(env_path, "a") as f:
        f.write(f"\nAPI_KEY={request.google_api_key}\n")
    
    return {"message": "Settings updated successfully"}