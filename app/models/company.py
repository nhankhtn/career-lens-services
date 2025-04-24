from datetime import datetime
from typing import List, Dict, Any, Optional
from pymongo.collection import Collection
from bson import ObjectId
from app.core.database import get_database, get_async_database


class CompanyModel:
    """MongoDB model for companies"""
    
    collection_name = "companies"
    
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
    async def create(cls, company_data: Dict[str, Any]) -> str:
        """Create a new company"""
        # Add timestamps
        company_data["created_at"] = datetime.now()
        company_data["updated_at"] = datetime.now()
        
        collection = await cls.get_async_collection()
        result = await collection.insert_one(company_data)
        return str(result.inserted_id)
    
    @classmethod
    async def find_by_id(cls, id: str) -> Optional[Dict[str, Any]]:
        """Find a company by ID"""
        collection = await cls.get_async_collection()
        result = await collection.find_one({"_id": ObjectId(id)})
        return result
    
    @classmethod
    async def find_by_name(cls, name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Find companies by name"""
        collection = await cls.get_async_collection()
        cursor = collection.find({"name": {"$regex": name, "$options": "i"}}).sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_recent(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Find most recent companies"""
        collection = await cls.get_async_collection()
        cursor = collection.find().sort("created_at", -1).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def find_by_date_range(cls, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Find companies within a date range"""
        collection = await cls.get_async_collection()
        cursor = collection.find({
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).sort("created_at", -1)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def update(cls, id: str, update_data: Dict[str, Any]) -> bool:
        """Update a company"""
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
        """Delete a company"""
        collection = await cls.get_async_collection()
        result = await collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
