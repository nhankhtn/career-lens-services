import time
import threading
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Dict, Any, List

from app.services.prediction_service import PredictionService
from app.models.career_history import CareerHistoryModel
from app.models.job_posting import JobPostingModel
from app.models.ai_error_log import AIErrorLogModel
from app.core.database import get_async_database

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        logger.info("Khởi tạo SchedulerService")
        self.prediction_service = PredictionService()
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        
        # Tạo thư mục để lưu kết quả dự đoán
        self.predictions_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "predictions"
        self.predictions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("SchedulerService đã được khởi tạo")

    def start_scheduler(self):
        """Khởi động scheduler"""
        logger.info("Bắt đầu khởi động scheduler")
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.info("Scheduler đã đang chạy")
            return
        
        def run_scheduler():
            logger.info("Thread scheduler đã bắt đầu")
            
            # Tạo event loop mới cho thread này
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def main():
                logger.info("Bắt đầu vòng lặp chính async")
                
                # Chạy dự đoán ngay lập tức
                logger.info("Chạy dự đoán lần đầu")
                try:
                    await self.run_prediction()
                    logger.info("Đã chạy dự đoán lần đầu")
                except Exception as e:
                    logger.error(f"Lỗi khi chạy dự đoán lần đầu: {e}")
                
                # Tiếp tục chạy dự đoán mỗi giây
                while not self.stop_event.is_set():
                    try:
                        # Đợi một chút trước khi chạy lại
                        logger.info("Đợi 1 giây trước khi chạy dự đoán tiếp")
                        await asyncio.sleep(1)  # Dùng asyncio.sleep thay vì time.sleep
                        
                        if self.stop_event.is_set():
                            break
                        
                        logger.info("Bắt đầu chạy dự đoán định kỳ")
                        await self.run_prediction()
                        logger.info("Đã chạy dự đoán định kỳ")
                    except Exception as e:
                        logger.error(f"Lỗi trong vòng lặp chính: {e}")
                        await asyncio.sleep(1)  # Đợi một chút trước khi thử lại
                
                logger.info("Kết thúc vòng lặp chính async")
            
            # Tạo task và chạy event loop
            loop.create_task(main())
            
            # Chạy event loop mãi mãi
            try:
                loop.run_forever()
            except Exception as e:
                logger.error(f"Lỗi trong event loop: {e}")
            finally:
                loop.close()
                logger.info("Đã đóng event loop")
            
            logger.info("Thread scheduler đã dừng")
        
        # Tạo và chạy thread
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Scheduler đã được khởi động")

    async def run_prediction(self):
        """Chạy một lần dự đoán"""
        logger.info("Bắt đầu chạy dự đoán")
        try:
            # Lấy tất cả job titles
            job_titles = await self._get_all_job_titles()
            logger.info(f"Đã lấy được {len(job_titles)} job titles")
            
            if not job_titles:
                logger.warning("Không có job titles để dự đoán")
                return
            
            # Dự đoán cho mỗi job title
            predictions = {}
            for job_title in job_titles:
                try:
                    logger.info(f"Đang dự đoán cho job title: {job_title}")
                    prediction = await self.prediction_service.predict_job_market(job_title=job_title)
                    
                    if isinstance(prediction.get('prediction_date'), datetime):
                        prediction['prediction_date'] = prediction['prediction_date'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    predictions[job_title] = prediction
                    logger.info(f"Đã hoàn thành dự đoán cho {job_title}")
                except Exception as e:
                    logger.error(f"Lỗi khi dự đoán cho job title {job_title}: {e}")
                    await self._save_error_log(
                        error_type="PredictionError",
                        error_message=str(e),
                        source="run_prediction",
                        additional_data={"job_title": job_title}
                    )
            
            # Lưu kết quả vào MongoDB
            if predictions:
                logger.info(f"Lưu {len(predictions)} dự đoán vào MongoDB")
                await self._save_to_mongodb(predictions)
                logger.info("Đã lưu dự đoán vào MongoDB")
            else:
                logger.warning("Không có dự đoán để lưu")
            
        except Exception as e:
            logger.error(f"Lỗi khi chạy dự đoán: {e}")
            await self._save_error_log(
                error_type="PredictionRunError",
                error_message=str(e),
                source="run_prediction"
            )
    
    async def _get_all_job_titles(self) -> List[str]:
        """Lấy tất cả các job title duy nhất từ MongoDB"""
        try:
            # Lấy dữ liệu từ MongoDB trong 6 tháng gần nhất
            cutoff_date = datetime.now() - timedelta(days=30 * 6)
            db = await get_async_database()
            collection = db["job_postings"]
            
            # Tạo query để lấy job postings trong khoảng thời gian
            query = {
                "date_posted": {
                    "$gte": cutoff_date,
                    "$lte": datetime.now()
                }
            }
            
            # Thực hiện query
            cursor = collection.find(query)
            job_postings = await cursor.to_list(length=None)
            
            if not job_postings:
                logger.warning("Không tìm thấy dữ liệu job postings trong MongoDB")
                await self._save_error_log(
                    error_type="DataNotFound",
                    error_message="Không tìm thấy dữ liệu job postings trong MongoDB",
                    source="_get_all_job_titles",
                    additional_data={"cutoff_date": str(cutoff_date)}
                )
                return []
            
            # Lấy tất cả các job title duy nhất
            unique_job_titles = set()
            for posting in job_postings:
                job_title = posting.get("job_title")
                if job_title:
                    unique_job_titles.add(job_title)
            
            job_titles = list(unique_job_titles)
            logger.info(f"Đã tìm thấy {len(job_titles)} job titles duy nhất")
            return job_titles
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy job titles từ MongoDB: {e}")
            await self._save_error_log(
                error_type="DatabaseError",
                error_message=str(e),
                source="_get_all_job_titles",
                additional_data={"cutoff_date": str(cutoff_date) if 'cutoff_date' in locals() else None}
            )
            return []

    async def _save_to_mongodb(self, predictions: Dict[str, Any]):
        """Lưu kết quả dự đoán vào MongoDB"""
        try:
            for job_title, prediction in predictions.items():
                # Lấy position_id (career_id) từ job posting data
                job_posting = await JobPostingModel.find_by_job_title(job_title)
                if not job_posting or not job_posting.get("position_id"):
                    logger.warning(f"Không tìm thấy position_id cho job title: {job_title}")
                    continue

                # Create document for MongoDB
                career_history_data = {
                    "career_id": job_posting["position_id"],  # Sử dụng position_id làm career_id
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
            await self._save_error_log(
                error_type="DatabaseError",
                error_message=str(e),
                source="_save_to_mongodb",
                additional_data={"predictions_count": len(predictions)}
            )
    
    def stop_scheduler(self):
        """Dừng scheduler"""
        logger.info("Dừng scheduler")
        self.stop_event.set()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            logger.info("Scheduler thread đã dừng")
        
        logger.info("Scheduler đã dừng")
    
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
    
    async def _save_error_log(self, error_type: str, error_message: str, source: str, additional_data: dict = None):
        """Lưu log lỗi vào MongoDB"""
        try:
            error_log = AIErrorLogModel(
                error_type=error_type,
                error_message=error_message,
                source=source,
                additional_data=additional_data
            )
            await error_log.save()
            logger.error(f"Đã lưu log lỗi: {error_type} - {error_message}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu log: {e}")
