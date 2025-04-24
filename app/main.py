from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import career_guidance
from app.core.database import get_database, get_async_database, close_mongo_connection
import logging
from app.services.scheduler_service import SchedulerService
import asyncio
import time
import threading
import schedule

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Tạo logger
logger = logging.getLogger(__name__)

app = FastAPI(title="IT Career Guidance & Job Market Prediction API", 
             description="API for IT career guidance and job market predictions based on historical data")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(career_guidance.router)

# Khởi tạo scheduler
scheduler = SchedulerService()  # Không truyền tham số

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and start scheduler when app starts"""
    try:
        # Test synchronous database connection
        db = get_database()
        logger.info("Successfully connected to synchronous database")
        
        # Test asynchronous database connection
        async_db = get_async_database()
        logger.info("Successfully connected to asynchronous database")
        
        # Khởi động scheduler khi ứng dụng bắt đầu
        scheduler.start_scheduler()
        logger.info("Scheduler service đã được khởi động")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.get("/")
async def root():
<<<<<<< HEAD
    # print(f"Connected to database: {db_name}")
    return {"message": "Welcome to the IT Career Guidance & Job Market Prediction API"} 
=======
    return {"message": "Welcome to the IT Career Guidance & Job Market Prediction API"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources when app shuts down"""
    try:
        # Dừng scheduler khi ứng dụng tắt
        scheduler.stop_scheduler()
        logger.info("Scheduler service đã dừng")
        
        # Đóng kết nối database
        close_mongo_connection()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise
>>>>>>> f6bb2d2aa0aacf489484f15a1b896e45d2dd328e
