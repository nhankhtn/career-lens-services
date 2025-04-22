import time
import schedule
import threading
import pandas as pd
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import os
from typing import Dict, List, Any, Optional

from app.services.prediction_service import PredictionService
from app.core.config import DATA_FILE_PATH
from app.models.career_history import CareerHistoryModel

class SchedulerService:
    """Dịch vụ chạy ngầm để dự đoán tiền lương và số lượng bài đăng tuyển dụng hàng ngày"""
    
    def __init__(self, data_file_path: str = DATA_FILE_PATH):
        """Khởi tạo dịch vụ với đường dẫn đến file dữ liệu"""
        self.data_file_path = data_file_path
        self.prediction_service = PredictionService(data_file_path)
        self.stop_event = threading.Event()
        self.scheduler_thread = None
        
        # Tạo thư mục để lưu kết quả dự đoán
        self.predictions_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "data" / "predictions"
        self.predictions_dir.mkdir(exist_ok=True, parents=True)
    
    def _get_popular_job_titles(self, limit: int = 10) -> List[str]:
        """Lấy các job title phổ biến nhất từ dữ liệu 6 tháng gần đây"""
        try:
            # Đọc dữ liệu
            df = pd.read_csv(self.data_file_path)
            
            # Chuyển đổi cột date_posted sang datetime
            df['date_posted'] = pd.to_datetime(df['date_posted'])
            
            # Lọc dữ liệu 6 tháng gần nhất
            cutoff_date = datetime.now() - timedelta(days=30 * 6)
            recent_data = df[df['date_posted'] >= cutoff_date]
            
            # Đếm số lượng mỗi job title và lấy top N
            if recent_data.empty:
                return ["Data Scientist", "Software Engineer", "Frontend Developer", 
                        "Backend Developer", "DevOps Engineer"]
            
            popular_jobs = recent_data['job_title'].value_counts().head(limit).index.tolist()
            return popular_jobs
            
        except Exception as e:
            print(f"Lỗi khi lấy job titles phổ biến: {e}")
            # Trả về danh sách mặc định nếu có lỗi
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
                
            print(f"Đã lưu kết quả dự đoán vào MongoDB")
        except Exception as e:
            print(f"Lỗi khi lưu kết quả dự đoán vào MongoDB: {e}")
    
    def _run_daily_predictions(self):
        """Chạy dự đoán hàng ngày cho các job title phổ biến"""
        print(f"Đang chạy dự đoán hàng ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Lấy danh sách job title phổ biến
        job_titles = self._get_popular_job_titles()
        
        # Tạo tên file dựa trên ngày hiện tại
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.predictions_dir / f"predictions_{date_str}.json"
        
        # Dự đoán cho mỗi job title
        predictions = {}
        for job_title in job_titles:
            # Dự đoán thị trường việc làm
            prediction = self.prediction_service.predict_job_market(
                job_title=job_title
            )
            
            # Chuyển đổi timestamp thành chuỗi để có thể serializer thành JSON
            if isinstance(prediction.get('prediction_date'), datetime):
                prediction['prediction_date'] = prediction['prediction_date'].strftime('%Y-%m-%d %H:%M:%S')
                
            predictions[job_title] = prediction
        
        # Lưu kết quả dự đoán vào file JSON
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu kết quả dự đoán vào file: {file_path}")
        except Exception as e:
            print(f"Lỗi khi lưu kết quả dự đoán vào file: {e}")
        
        # Lưu kết quả dự đoán vào MongoDB
        asyncio.run(self._save_to_mongodb(predictions))
    
    def start_scheduler(self):
        """Bắt đầu dịch vụ chạy ngầm với lịch trình hàng ngày"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            print("Dịch vụ dự đoán đã được khởi động")
            return
        
        # Đặt lịch chạy dự đoán mỗi ngày lúc 00:00
        schedule.every().day.at("00:00").do(self._run_daily_predictions)
        
        # Chạy lần đầu ngay khi khởi động dịch vụ
        self._run_daily_predictions()
        
        # Đặt cờ dừng về False
        self.stop_event.clear()
        
        # Tạo thread mới để chạy ngầm dịch vụ
        def run_scheduler():
            while not self.stop_event.is_set():
                schedule.run_pending()
                time.sleep(60)  # Kiểm tra mỗi phút
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("Dịch vụ dự đoán đã được khởi động thành công")
    
    def stop_scheduler(self):
        """Dừng dịch vụ chạy ngầm"""
        self.stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            print("Dịch vụ dự đoán đã dừng")
    
    async def get_latest_predictions_mongodb(self, limit: int = 10) -> Dict[str, Any]:
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
            return {"status": "error", "message": str(e)}
    
    def get_latest_predictions(self) -> Dict[str, Any]:
        """Lấy kết quả dự đoán gần nhất từ file"""
        try:
            # Tìm file dự đoán mới nhất
            prediction_files = list(self.predictions_dir.glob("predictions_*.json"))
            if not prediction_files:
                return {"status": "error", "message": "Không tìm thấy dữ liệu dự đoán"}
            
            # Sắp xếp theo ngày mới nhất
            latest_file = max(prediction_files, key=lambda x: x.stat().st_mtime)
            
            # Đọc file
            with open(latest_file, 'r', encoding='utf-8') as f:
                predictions = json.load(f)
            
            return {
                "status": "success",
                "source": "file",
                "date": latest_file.stem.replace("predictions_", ""),
                "predictions": predictions
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)} 