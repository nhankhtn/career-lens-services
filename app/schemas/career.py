from pydantic import BaseModel
from typing import Optional, List


class CareerGuidanceRequest(BaseModel):
    """Request model for career guidance"""
    education: str
    skills: List[str]
    experience: str
    certificates: str
    target_job: str
    
    
    class Config:
        schema_extra = {
            "example": {
                "education": "Bachelor's in Computer Science",
                "skills": ["Python", "SQL", "Basic Machine Learning"],
                "experience": "1 year as Junior Developer",
                "certificates": "AWS Cloud Practitioner",
                "target_job": "Data Scientist"
            }
        }


class CareerGuidanceResponse(BaseModel):
    """Response model for career guidance"""
    status: str
    guidance: Optional[List[str]] = None
    message: Optional[str] = None
    relevant_jobs_count: Optional[int] = None 