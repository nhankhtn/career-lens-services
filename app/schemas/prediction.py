from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class JobPredictionRequest(BaseModel):
    """Request model for job prediction"""
    job_title: str
    position: Optional[str] = None
    experience_level: Optional[str] = None
    skills: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_title": "Data Scientist",
                "position": "Data Scientist",
                "experience_level": "Mid-level",
                "skills": ["Python", "Machine Learning", "SQL", "Data Analysis"]
            }
        }


class SalaryPrediction(BaseModel):
    """Model for salary prediction"""
    min_salary: float
    max_salary: float
    avg_salary: float
    trend: str  # "increasing", "decreasing", or "stable"
    confidence: float  # 0-1 confidence level


class JobPostingsPrediction(BaseModel):
    """Model for job postings prediction"""
    weekly_postings: int
    trend: str  # "increasing", "decreasing", or "stable"
    confidence: float  # 0-1 confidence level
    top_companies: List[str]


class JobPredictionResponse(BaseModel):
    """Response model for job prediction"""
    status: str
    message: Optional[str] = None
    prediction_date: datetime
    job_title: str
    salary_prediction: Optional[SalaryPrediction] = None
    job_postings_prediction: Optional[JobPostingsPrediction] = None 