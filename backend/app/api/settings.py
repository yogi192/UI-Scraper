from fastapi import APIRouter, HTTPException, Depends
from app.config import settings as app_settings
from pydantic import BaseModel
import os
import litellm
import asyncio

router = APIRouter()

class UpdateSettingsRequest(BaseModel):
    google_api_key: str

class SettingsResponse(BaseModel):
    has_google_api_key: bool

@router.get("/", response_model=SettingsResponse)
async def get_settings():
    return {
        "has_google_api_key": bool(app_settings.google_api_key)
    }

@router.put("/")
async def update_settings(request: UpdateSettingsRequest):
    # Test the API key before saving
    try:
        test_response = await litellm.acompletion(
            model="gemini/gemini-2.0-flash-exp",
            api_key=request.google_api_key,
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=10
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid API key: {str(e)}")
    
    # Update environment variable
    os.environ["GOOGLE_API_KEY"] = request.google_api_key
    
    # Update settings
    app_settings.google_api_key = request.google_api_key
    
    # Update .env file - check both possible locations
    # Try Docker mounted path first
    env_paths = [
        "/app/.env",  # Docker mounted volume
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")  # Local path
    ]
    
    env_path = None
    for path in env_paths:
        if os.path.exists(path):
            env_path = path
            break
    
    if not env_path:
        # If no .env exists, create one in the mounted volume
        env_path = "/app/.env"
    
    # Read existing .env file
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
        
        # Update or add GOOGLE_API_KEY
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith("GOOGLE_API_KEY="):
                lines[i] = f"GOOGLE_API_KEY={request.google_api_key}\n"
                key_found = True
                break
        
        if not key_found:
            lines.append(f"GOOGLE_API_KEY={request.google_api_key}\n")
        
        # Write back to file
        with open(env_path, "w") as f:
            f.writelines(lines)
    else:
        # Create new .env file
        with open(env_path, "w") as f:
            f.write(f"GOOGLE_API_KEY={request.google_api_key}\n")
    
    return {"message": "Settings updated successfully"}