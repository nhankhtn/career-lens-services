from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import DATABASE_URL

class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

class AIErrorLogModel(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias="_id")
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)
    additional_data: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    async def save(cls, error_data: dict) -> 'AIErrorLogModel':
        """Create a new error log entry in the database"""
        client = AsyncIOMotorClient(DATABASE_URL)
        db = client.get_database()
        collection = db.ai_error_logs

        # Add timestamps
        error_data['created_at'] = datetime.now()
        error_data['updated_at'] = datetime.now()

        # Insert document
        result = await collection.insert_one(error_data)
        
        # Get the inserted document
        inserted_doc = await collection.find_one({"_id": result.inserted_id})
        
        # Convert to model instance
        return cls(**inserted_doc)
