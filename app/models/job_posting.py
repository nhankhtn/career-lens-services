from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from bson import ObjectId
from app.core.database import get_database, get_async_database
from app.models.interfaces import IJobPosting


class JobPostingModel:
    """MongoDB model for job postings"""
    
    collection_name = "job_postings"
    
    @classmethod
    def get_collection(cls) -> Collection:
        """Get MongoDB collection (synchronous)"""
        db = get_database()
        return db[cls.collection_name]
    
    @classmethod
    async def get_async_collection(cls):
        """Get MongoDB collection (asynchronous)"""
        db = await get_async_database()
        return db[cls.collection_name]
    
    @classmethod
    async def create(cls, job_posting_data: Dict[str, Any]) -> str:
        """Create a new job posting"""
        # Add timestamps
        job_posting_data["created_at"] = datetime.now()
        job_posting_data["updated_at"] = datetime.now()
        
        # Set default date_posted if not provided
        if "date_posted" not in job_posting_data:
            job_posting_data["date_posted"] = datetime.now()
            
        collection = await cls.get_async_collection()
        result = await collection.insert_one(job_posting_data)
        return str(result.inserted_id)
    
    @classmethod
    async def find_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Find a job posting by ID"""
        collection = await cls.get_async_collection()
        result = await collection.find_one({"_id": ObjectId(id)})
        return result
    
    @classmethod
    async def find_by_job_title(cls, job_title: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Find job postings by job title"""
        collection = await cls.get_async_collection()
        cursor = collection.find({"job_title": {"$regex": job_title, "$options": "i"}}).sort("date_posted", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Find most recent job postings"""
        collection = await cls.get_async_collection()
        cursor = collection.find().sort("date_posted", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_by_date_range(cls, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Find job postings within a date range"""
        collection = await cls.get_async_collection()
        cursor = collection.find({
            "date_posted": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("date_posted", -1)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def update(cls, id: str, update_data: Dict[str, Any]) -> bool:
        """Update a job posting"""
        # Add updated timestamp
        update_data["updated_at"] = datetime.now()
        
        collection = await cls.get_async_collection()
        result = await collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    async def delete(cls, id: str) -> bool:
        """Delete a job posting"""
        collection = await cls.get_async_collection()
        result = await collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    @classmethod
    async def find_recent_months(cls, months: int = 6) -> List[Dict[str, Any]]:
        """Find job postings from the last N months"""
        # Calculate cutoff date
        cutoff_date = datetime.now().replace(day=1)  # First day of current month
        for _ in range(months):
            # Go back to previous month
            if cutoff_date.month == 1:
                cutoff_date = cutoff_date.replace(year=cutoff_date.year - 1, month=12)
            else:
                cutoff_date = cutoff_date.replace(month=cutoff_date.month - 1)
                
        collection = await cls.get_async_collection()
        cursor = collection.find({
            "date_posted": {"$gte": cutoff_date}
        }).sort("date_posted", -1)
        return await cursor.to_list(length=None) 