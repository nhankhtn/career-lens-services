from datetime import datetime
from typing import Dict, List, Any, Optional
from bson import ObjectId
from app.core.database import get_async_database

class CareerModel:
    """Model for managing careers in MongoDB"""
    
    @staticmethod
    async def get_collection():
        """Get MongoDB collection"""
        db = await get_async_database()
        return db["careers"]
    
    @staticmethod
    async def find_by_job_title(job_title: str) -> Optional[Dict[str, Any]]:
        """Find career by job title"""
        try:
            collection = await CareerModel.get_collection()
            career = await collection.find_one({"job_title": job_title})
            return career
        except Exception as e:
            print(f"Error finding career by job title: {e}")
            return None
    
    @staticmethod
    async def create(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create new career"""
        try:
            collection = await CareerModel.get_collection()
            data["created_at"] = datetime.now()
            data["updated_at"] = datetime.now()
            result = await collection.insert_one(data)
            data["_id"] = result.inserted_id
            return data
        except Exception as e:
            print(f"Error creating career: {e}")
            return None
    
    @staticmethod
    async def find_all() -> List[Dict[str, Any]]:
        """Find all careers"""
        try:
            collection = await CareerModel.get_collection()
            careers = await collection.find().to_list(length=None)
            return careers
        except Exception as e:
            print(f"Error finding all careers: {e}")
            return []
    
    @staticmethod
    async def update(career_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update career"""
        try:
            collection = await CareerModel.get_collection()
            data["updated_at"] = datetime.now()
            await collection.update_one(
                {"_id": ObjectId(career_id)},
                {"$set": data}
            )
            return await collection.find_one({"_id": ObjectId(career_id)})
        except Exception as e:
            print(f"Error updating career: {e}")
            return None
    
    @staticmethod
    async def delete(career_id: str) -> bool:
        """Delete career"""
        try:
            collection = await CareerModel.get_collection()
            result = await collection.delete_one({"_id": ObjectId(career_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting career: {e}")
            return False 