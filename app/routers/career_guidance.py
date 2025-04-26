from fastapi import APIRouter, Depends, HTTPException
from app.schemas.career import CareerGuidanceRequest, CareerGuidanceResponse
from app.services.openai_service import OpenAIService
from app.core.config import DATA_FILE_PATH
from typing import Dict, List, Any

router = APIRouter(
    prefix="/career",
    tags=["career"],
    responses={404: {"description": "Not found"}},
)

def get_openai_service():
    """Dependency to get OpenAI service instance"""
    return OpenAIService(DATA_FILE_PATH)

@router.post("/guidance", response_model=CareerGuidanceResponse)
async def get_career_guidance(
    request: CareerGuidanceRequest,
    openai_service: OpenAIService = Depends(get_openai_service)
):
    """
    Get personalized career guidance based on user profile and target job.
    Response will be in Vietnamese.
    """
    response = openai_service.generate_career_guidance(
        education=request.education,
        skills=request.skills,
        experience=request.experience,
        certificates=request.certificates,
        target_job=request.target_job
    )
    
    if response["status"] == "error":
        raise HTTPException(status_code=500, detail=response["message"])
    
    # No longer need to split the guidance into an array
    # The guidance is already a string from the OpenAI service
    
    return response
