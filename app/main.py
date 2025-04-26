from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import career_guidance
from app.core.database import get_database, get_async_database, close_mongo_connection
import logging
from app.services.scheduler_service import SchedulerService
from app.middlewares.auth_middleware import AuthMiddleware

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IT Career Guidance & Job Market Prediction API", 
    description="API for IT career guidance and job market predictions based on historical data"
)

# Thêm middleware xác thực
app.add_middleware(AuthMiddleware)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://career-lens-api.onrender.com", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(career_guidance.router)

# Khởi tạo scheduler
scheduler = SchedulerService()

# @app.on_event("startup")
# def startup_event():
#     """Initialize database connection and start scheduler when app starts"""
#     logger.info("Bắt đầu khởi động app")
#     try:
#         # Test synchronous database connection
#         db = get_database()
#         logger.info("Successfully connected to synchronous database")
        
#         # Test asynchronous database connection
#         async_db = get_async_database()
#         logger.info("Successfully connected to asynchronous database")
        
#         # Khởi động scheduler
#         logger.info("Đang khởi động scheduler...")
#         scheduler.start_scheduler()   # KHÔNG await
#         logger.info("Scheduler đã được khởi động thành công")
        
#     except Exception as e:
#         logger.error(f"Lỗi khi khởi động: {e}")
#         raise

@app.get("/")
async def root():
    # print(f"Connected to database: {db_name}")
    return {"message": "Welcome to the IT Career Guidance & Job Market Prediction API"} 

@app.on_event("shutdown")
def shutdown_event():
    """Cleanup resources when app shuts down"""
    logger.info("Bắt đầu dừng app")
    try:
        # Dừng scheduler
        logger.info("Đang dừng scheduler...")
        scheduler.stop_scheduler()   # KHÔNG await
        logger.info("Scheduler đã được dừng thành công")
        
        # Đóng kết nối database
        close_mongo_connection()
        logger.info("Database connections closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise
