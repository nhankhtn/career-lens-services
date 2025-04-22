from fastapi import APIRouter, Depends, HTTPException
from app.schemas.prediction import JobPredictionRequest, JobPredictionResponse
from app.services.prediction_service import PredictionService
from app.core.config import DATA_FILE_PATH
from typing import Dict, List, Any

router = APIRouter(
    prefix="/prediction",
    tags=["prediction"],
    responses={404: {"description": "Not found"}},
)

def get_prediction_service():
    """Dependency to get Prediction service instance"""
    return PredictionService(DATA_FILE_PATH)

@router.post("/job-market", response_model=JobPredictionResponse)
async def predict_job_market(
    request: JobPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service)
):
    """
    Predict job salary and job postings for the next week using fake model weights
    based on historical data from the past 6 months
    """
    response = prediction_service.predict_job_market(
        job_title=request.job_title,
        position=request.position,
        experience_level=request.experience_level,
        skills=request.skills
    )
    
    if response["status"] == "error":
        raise HTTPException(status_code=500, detail=response["message"])
    
    return response 