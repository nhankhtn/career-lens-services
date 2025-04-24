import os
import motor.motor_asyncio
from pymongo import MongoClient
from pymongo.database import Database
from app.core.config import DATABASE_URL
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB client instances - keep both sync and async clients
_mongo_client: Optional[MongoClient] = None
_mongo_async_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
_db: Optional[Database] = None
_async_db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

def get_database() -> Database:
    """Get MongoDB database instance (synchronous)"""
    global _mongo_client, _db
    if not _mongo_client:
        try:
            logger.info(f"Attempting to connect to MongoDB at: {DATABASE_URL}")
            _mongo_client = MongoClient(DATABASE_URL)
            
            # Test the connection
            _mongo_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Extract database name from connection string
            db_name = DATABASE_URL.split("/")[-1].split("?")[0]
            if not db_name:
                db_name = "historical-preservation"  # Default database name
                
            _db = _mongo_client[db_name]
            
            # Log database information
            logger.info(f"Connected to database: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
            
    return _db

def get_async_database():
    """Get MongoDB database instance (asynchronous)"""
    global _mongo_async_client, _async_db
    if not _mongo_async_client:
        try:
            logger.info(f"Attempting to create async MongoDB connection at: {DATABASE_URL}")
            _mongo_async_client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
            
            # Extract database name from connection string
            db_name = DATABASE_URL.split("/")[-1].split("?")[0]
            if not db_name:
                db_name = "historical-preservation"  # Default database name
                
            _async_db = _mongo_async_client[db_name]
            logger.info(f"Async database connection established: {db_name}")
            
        except Exception as e:
            logger.error(f"Failed to create async MongoDB connection: {str(e)}")
            raise
            
    return _async_db

def close_mongo_connection():
    """Close MongoDB connection"""
    global _mongo_client, _mongo_async_client
    try:
        if _mongo_client:
            _mongo_client.close()
            _mongo_client = None
            logger.info("Synchronous MongoDB connection closed")
            
        if _mongo_async_client:
            _mongo_async_client.close()
            _mongo_async_client = None
            logger.info("Asynchronous MongoDB connection closed")
            
    except Exception as e:
        logger.error(f"Error closing MongoDB connections: {str(e)}")
        raise 