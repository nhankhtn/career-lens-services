from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)


class SalaryPrediction(BaseModel):
    min_salary: float
    max_salary: float
    avg_salary: float
    trend: str  # "increasing", "decreasing", or "stable"
    confidence: float


class JobPostingsPrediction(BaseModel):
    weekly_postings: int
    trend: str  # "increasing", "decreasing", or "stable"
    confidence: float
    top_companies: List[str]


class ICareerHistory(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    job_title: str
    status: str
    prediction_date: datetime
    salary_prediction: SalaryPrediction
    job_postings_prediction: JobPostingsPrediction
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }


class IJobPosting(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    job_title: str
    salary_min: float
    salary_max: Optional[float] = None
    company_id: PyObjectId
    job_description: str
    position: PyObjectId
    yof: PyObjectId  # years of experience
    date_posted: datetime = datetime.now()
    location: str
    skills: Optional[List[PyObjectId]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        } 