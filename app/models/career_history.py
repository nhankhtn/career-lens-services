from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from bson import ObjectId
from app.core.database import get_database, get_async_database
from app.models.interfaces import ICareerHistory


class CareerHistoryModel:
    """MongoDB model for career history predictions"""
    
    collection_name = "career_histories"
    
    @classmethod
    def get_collection(cls) -> Collection:
        """Get MongoDB collection (synchronous)"""
        db = get_database()
        return db[cls.collection_name]
    
    @classmethod
    def get_async_collection(cls):
        """Get MongoDB collection (asynchronous)"""
        db = get_async_database()
        return db[cls.collection_name]
    
    @classmethod
    async def create(cls, career_history_data: Dict[str, Any]) -> str:
        """Create a new career history prediction record"""
        # Add timestamps
        career_history_data["created_at"] = datetime.now()
        career_history_data["updated_at"] = datetime.now()
        
        # Đảm bảo cấu trúc dữ liệu đúng
        if "job_postings_prediction" not in career_history_data:
            career_history_data["job_postings_prediction"] = {}
            
        # Thêm các trường mới nếu chưa có
        job_postings_prediction = career_history_data["job_postings_prediction"]
        if "total_openings" not in job_postings_prediction:
            job_postings_prediction["total_openings"] = 0
        if "average_openings_per_posting" not in job_postings_prediction:
            job_postings_prediction["average_openings_per_posting"] = 0
            
        collection = cls.get_async_collection()
        result = await collection.insert_one(career_history_data)
        return str(result.inserted_id)
    
    @classmethod
    async def find_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Find a career history prediction by ID"""
        collection = cls.get_async_collection()
        result = await collection.find_one({"_id": ObjectId(id)})
        return result
    
    @classmethod
    async def find_by_job_title(cls, job_title: str) -> List[Dict[str, Any]]:
        """Find career history predictions by job title"""
        collection = cls.get_async_collection()
        cursor = collection.find({"job_title": job_title}).sort("prediction_date", -1)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_recent(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """Find most recent career history predictions"""
        collection = cls.get_async_collection()
        cursor = collection.find().sort("prediction_date", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_by_date_range(cls, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Find career history predictions within a date range"""
        collection = cls.get_async_collection()
        cursor = collection.find({
            "prediction_date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("prediction_date", -1)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def update(cls, id: str, update_data: Dict[str, Any]) -> bool:
        """Update a career history prediction record"""
        # Add updated timestamp
        update_data["updated_at"] = datetime.now()
        
        # Đảm bảo cấu trúc dữ liệu đúng
        if "job_postings_prediction" in update_data:
            job_postings_prediction = update_data["job_postings_prediction"]
            if "total_openings" not in job_postings_prediction:
                job_postings_prediction["total_openings"] = 0
            if "average_openings_per_posting" not in job_postings_prediction:
                job_postings_prediction["average_openings_per_posting"] = 0
        
        collection = cls.get_async_collection()
        result = await collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    async def delete(cls, id: str) -> bool:
        """Delete a career history prediction record"""
        collection = cls.get_async_collection()
        result = await collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0