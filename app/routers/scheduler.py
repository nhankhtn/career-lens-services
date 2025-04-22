from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.scheduler_service import SchedulerService
from app.core.config import DATA_FILE_PATH
from typing import Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
    responses={404: {"description": "Not found"}},
)

# Singleton instance of the scheduler service
_scheduler_service = None

def get_scheduler_service():
    """Dependency để lấy instance của Scheduler service"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService(DATA_FILE_PATH)
    return _scheduler_service

class ServiceResponse(BaseModel):
    """Response model cho các endpoint của scheduler"""
    status: str
    message: str

@router.post("/start", response_model=ServiceResponse)
async def start_scheduler(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
):
    """
    Bắt đầu dịch vụ dự đoán tiền lương và bài đăng tuyển dụng hàng ngày.
    Dịch vụ sẽ chạy mỗi ngày lúc 00:00 và lưu kết quả vào file và MongoDB.
    """
    try:
        scheduler_service.start_scheduler()
        return {
            "status": "success",
            "message": "Dịch vụ dự đoán đã được khởi động thành công"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop", response_model=ServiceResponse)
async def stop_scheduler(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
):
    """
    Dừng dịch vụ dự đoán tiền lương và bài đăng tuyển dụng hàng ngày.
    """
    try:
        scheduler_service.stop_scheduler()
        return {
            "status": "success",
            "message": "Dịch vụ dự đoán đã dừng thành công"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest-predictions")
async def get_latest_predictions(
    source: Optional[str] = Query(None, description="Nguồn dữ liệu (file hoặc mongodb)"),
    limit: int = Query(10, description="Số lượng bản ghi tối đa để lấy từ MongoDB"),
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
):
    """
    Lấy kết quả dự đoán mới nhất từ file lưu trữ hoặc MongoDB.
    Nếu không chỉ định nguồn, ưu tiên lấy từ MongoDB nếu có, nếu không sẽ lấy từ file.
    """
    if source == "file":
        # Lấy từ file
        result = scheduler_service.get_latest_predictions()
    elif source == "mongodb":
        # Lấy từ MongoDB
        result = await scheduler_service.get_latest_predictions_mongodb(limit)
    else:
        # Thử lấy từ MongoDB trước, nếu không có thì lấy từ file
        mongo_result = await scheduler_service.get_latest_predictions_mongodb(limit)
        if mongo_result["status"] == "success":
            result = mongo_result
        else:
            result = scheduler_service.get_latest_predictions()
    
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result

@router.post("/run-now", response_model=ServiceResponse)
async def run_predictions_now(
    scheduler_service: SchedulerService = Depends(get_scheduler_service)
):
    """
    Chạy dự đoán ngay lập tức, không cần đợi lịch trình.
    Hữu ích để test hoặc cập nhật dự đoán theo yêu cầu.
    Kết quả sẽ được lưu vào cả file và MongoDB.
    """
    try:
        scheduler_service._run_daily_predictions()
        return {
            "status": "success",
            "message": "Đã chạy dự đoán thành công"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 