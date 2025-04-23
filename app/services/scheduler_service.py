import time
import schedule
import threading
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import os

from app.services.prediction_service import PredictionService
from app.models.career_history import CareerHistoryModel
from app.models.job_posting import JobPostingModel
from app.models.ai_error_log import AIErrorLogModel

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Tạo logger
logger = logging.getLogger(__name__)

class SchedulerService:
    """Dịch vụ chạy ngầm để dự đoán tiền lương và số lượng bài đăng tuyển dụng hàng ngày"""
    
    def __init__(self):
        """Khởi tạo dịch vụ"""
        self.prediction_service = PredictionService()
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        self.loop = None  # Thêm biến để lưu event loop
        
        # Tạo thư mục để lưu kết quả dự đoán
        self.predictions_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "predictions"
        self.predictions_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info("SchedulerService đã được khởi tạo")
    
    async def _get_popular_job_titles(self, limit: int = 10) -> List[str]:
        """Lấy các job title phổ biến nhất từ MongoDB trong 6 tháng gần đây"""
        try:
            # Lấy dữ liệu từ MongoDB trong 6 tháng gần nhất
            cutoff_date = datetime.now() - timedelta(days=30 * 6)
            job_postings = await JobPostingModel.find_by_date_range(cutoff_date, datetime.now())
            
            if not job_postings:
                logger.warning("Không tìm thấy dữ liệu job postings trong MongoDB")
                return ["Data Scientist", "Software Engineer", "Frontend Developer", 
                        "Backend Developer", "DevOps Engineer"]
            
            # Đếm số lượng mỗi job title
            job_counts = {}
            for posting in job_postings:
                job_title = posting.get("job_title")
                if job_title:
                    job_counts[job_title] = job_counts.get(job_title, 0) + 1
            
            # Sắp xếp và lấy top N
            popular_jobs = sorted(job_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            return [job[0] for job in popular_jobs]
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy job titles phổ biến từ MongoDB: {e}")
            return ["Data Scientist", "Software Engineer", "Frontend Developer", 
                    "Backend Developer", "DevOps Engineer"]
    
    async def _save_to_mongodb(self, predictions: Dict[str, Any]):
        """Lưu kết quả dự đoán vào MongoDB"""
        try:
            for job_title, prediction in predictions.items():
                # Create document for MongoDB
                career_history_data = {
                    "job_title": job_title,
                    "status": prediction["status"],
                    "prediction_date": datetime.strptime(prediction["prediction_date"], "%Y-%m-%d %H:%M:%S") 
                        if isinstance(prediction["prediction_date"], str) else prediction["prediction_date"],
                    "salary_prediction": prediction["salary_prediction"],
                    "job_postings_prediction": prediction["job_postings_prediction"]
                }
                
                # Save to MongoDB
                await CareerHistoryModel.create(career_history_data)
                
            logger.info("Đã lưu kết quả dự đoán vào MongoDB")
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả dự đoán vào MongoDB: {e}")
    
    def start_scheduler(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.info("Dịch vụ dự đoán đã được khởi động")
            return

        self.loop = asyncio.new_event_loop()

        # Tạo thread chạy event loop
        def loop_thread():
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        threading.Thread(target=loop_thread, daemon=True).start()

        # Đặt lịch với schedule
        schedule.every(1).minutes.do(
            lambda: asyncio.run_coroutine_threadsafe(self._run_daily_predictions(), self.loop)
        )

        # Tạo thread chạy schedule
        def run_scheduler():
            while not self.stop_event.is_set():
                schedule.run_pending()
                # logger.info("Đã kiểm tra lịch trình")
                time.sleep(1)

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def _run_daily_predictions_sync(self):
        """Chạy dự đoán hàng ngày (synchronous version)"""
        try:
            logger.info(f"Bắt đầu chạy dự đoán: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # Chạy async function trong event loop hiện tại mà không block
            self.loop.create_task(self._run_daily_predictions())
        except Exception as e:
            logger.error(f"Lỗi khi chạy dự đoán hàng ngày: {e}")
    
    async def _run_daily_predictions(self):
        """Chạy dự đoán hàng ngày cho các job title phổ biến"""
        logger.info(f"Đang chạy dự đoán hàng ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Lấy danh sách job title phổ biến từ MongoDB
            job_titles = await self._get_popular_job_titles()
            
            # Dự đoán cho mỗi job title
            predictions = {}
            for job_title in job_titles:
                try:
                    logger.info(f"Đang dự đoán cho job title: {job_title}")
                    prediction = await self.prediction_service.predict_job_market(
                        job_title=job_title
                    )
                    
                    if isinstance(prediction.get('prediction_date'), datetime):
                        prediction['prediction_date'] = prediction['prediction_date'].strftime('%Y-%m-%d %H:%M:%S')
                        
                    predictions[job_title] = prediction
                    logger.info(f"Đã hoàn thành dự đoán cho {job_title}")
                except Exception as e:
                    logger.error(f"Lỗi khi dự đoán cho job title {job_title}: {e}")
                    await self._save_error_log(
                        error_type="PredictionError",
                        error_message=str(e),
                        source="run_daily_predictions",
                        stack_trace=str(e.__traceback__),
                        additional_data={"job_title": job_title}
                    )
                    continue
            print(predictions)
            # Lưu kết quả vào MongoDB
            await self._save_to_mongodb(predictions)
            logger.info("Đã hoàn thành quá trình dự đoán và lưu kết quả")
            
        except Exception as e:
            logger.error(f"Lỗi khi chạy dự đoán hàng ngày: {e}")
            await self._save_error_log(
                error_type="SystemError",
                error_message=str(e),
                source="run_daily_predictions",
                stack_trace=str(e.__traceback__)
            )
    
    def stop_scheduler(self):
        """Dừng dịch vụ chạy ngầm"""
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        if self.loop:
            self.loop.close()
        logger.info("Dịch vụ dự đoán đã dừng")
    
    async def get_latest_predictions(self, limit: int = 10) -> Dict[str, Any]:
        """Lấy kết quả dự đoán gần nhất từ MongoDB"""
        try:
            # Lấy dữ liệu từ MongoDB
            results = await CareerHistoryModel.find_recent(limit)
            if not results:
                return {"status": "error", "message": "Không tìm thấy dữ liệu dự đoán trong MongoDB"}
            
            # Nhóm kết quả theo job_title
            predictions = {}
            for result in results:
                job_title = result["job_title"]
                # Chuyển ObjectId thành string
                if "_id" in result:
                    result["_id"] = str(result["_id"])
                # Chuyển datetime thành string để có thể JSON serialize
                if "prediction_date" in result and isinstance(result["prediction_date"], datetime):
                    result["prediction_date"] = result["prediction_date"].strftime('%Y-%m-%d %H:%M:%S')
                if "created_at" in result and isinstance(result["created_at"], datetime):
                    result["created_at"] = result["created_at"].strftime('%Y-%m-%d %H:%M:%S')
                if "updated_at" in result and isinstance(result["updated_at"], datetime):
                    result["updated_at"] = result["updated_at"].strftime('%Y-%m-%d %H:%M:%S')
                    
                predictions[job_title] = result
                
            return {
                "status": "success",
                "source": "mongodb",
                "predictions": predictions
            }
                
        except Exception as e:
            logger.error(f"Lỗi khi lấy dự đoán từ MongoDB: {e}")
            return {"status": "error", "message": str(e)}
    
    async def _save_error_log(self, error_type: str, error_message: str, source: str, stack_trace: str = None, additional_data: dict = None):
        """Lưu log lỗi vào MongoDB"""
        try:
            error_log = ErrorLogModel(
                error_type=error_type,
                error_message=error_message,
                source=source,
                stack_trace=stack_trace,
                additional_data=additional_data
            )
            await error_log.save()
            logger.error(f"Đã lưu log lỗi: {error_type} - {error_message}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu log: {e}")