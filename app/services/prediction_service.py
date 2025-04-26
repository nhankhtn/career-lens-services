import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from app.models.ai_error_log import AIErrorLogModel
from app.models.career_history import CareerHistoryModel
from app.models.job_posting import JobPostingModel
from app.models.company import CompanyModel
from app.core.database import get_async_database

# Tạo logger
logger = logging.getLogger(__name__)

class PredictionService:
    """Service to predict job salaries and postings using fake models with fake weights"""
    
    def __init__(self):
        """Initialize prediction service"""
        self.data = None  # Không load data ngay lập tức
        self.salary_weights = {
            'job_title': 0.4,
            'position': 0.3,
            'experience_level': 0.3,
            'skills_match': 0.2,
            'market_trend': 0.2,
            'random_factor': 0.1
        }
        
        self.postings_weights = {
            'job_title': 0.35,
            'skills_demand': 0.25,
            'market_growth': 0.2,
            'seasonality': 0.1,
            'random_factor': 0.1
        }
        logger.info("PredictionService đã được khởi tạo")
    
    async def _load_data(self) -> pd.DataFrame:
        """Load job postings data from MongoDB"""
        try:
            # Lấy dữ liệu từ MongoDB
            cutoff_date = datetime.now() - timedelta(days=30 * 6)
            job_postings = await JobPostingModel.find_by_date_range(cutoff_date, datetime.now())
            
            if not job_postings:
                logger.warning("Không tìm thấy dữ liệu job postings trong MongoDB")
                return pd.DataFrame(columns=['job_title', 'salary_min', 'salary_max', 
                                         'company_id', 'job_description', 'position', 
                                         'yof', 'date_posted', 'skills'])
            
            # Chuyển đổi dữ liệu MongoDB thành DataFrame
            data = []
            for posting in job_postings:
                data.append({
                    'job_title': posting.get('job_title'),
                    'salary_min': posting.get('salary_min'),
                    'salary_max': posting.get('salary_max'),
                    'company_id': posting.get('company_id'),
                    'job_description': posting.get('job_description'),
                    'position': posting.get('position'),
                    'yof': posting.get('yof'),
                    'date_posted': posting.get('date_posted'),
                    'skills': posting.get('skills')
                })
            
            df = pd.DataFrame(data)
            df['date_posted'] = pd.to_datetime(df['date_posted'])
            return df
            
        except Exception as e:
            logger.error(f"Lỗi khi tải dữ liệu từ MongoDB: {e}")
            return pd.DataFrame(columns=['job_title', 'salary_min', 'salary_max', 
                                     'company_id', 'job_description', 'position', 
                                     'yof', 'date_posted', 'skills'])
    
    def _get_recent_data(self, months: int = 6) -> pd.DataFrame:
        """Get data from the last N months"""
        if self.data.empty:
            return self.data
            
        cutoff_date = datetime.now() - timedelta(days=30 * months)
        return self.data[self.data['date_posted'] >= cutoff_date]
    
    def _calculate_experience_factor(self, experience_level: str) -> float:
        """Calculate a factor based on experience level"""
        level_factors = {
            "Intern": 0.5,
            "Fresher": 0.7,
            "Junior": 0.8,
            "Mid-level": 1.0,
            "Senior": 1.3,
            "Lead": 1.5,
            "Principal/Expert": 1.8
        }
        return level_factors.get(experience_level, 1.0)
    
    def _calculate_skills_factor(self, requested_skills: List[str], job_data: pd.DataFrame) -> float:
        """Calculate a factor based on skills match"""
        if not requested_skills or job_data.empty:
            return 1.0
            
        # Create a set of all skills across job listings (splitting the skills column by ';')
        all_skills = set()
        for skills_str in job_data['skills'].dropna():
            skills = [skill.strip() for skill in skills_str.split(';')]
            all_skills.update(skills)
        
        # Calculate the proportion of requested skills that are in demand
        if not all_skills:
            return 1.0
            
        matching_skills = sum(1 for skill in requested_skills if skill in all_skills)
        return 0.8 + (0.4 * (matching_skills / len(requested_skills)))
    
    def _add_random_variation(self, base_value: float, variation_percentage: float = 0.1) -> float:
        """Add random variation to a value within a percentage range"""
        variation = base_value * variation_percentage
        return base_value + random.uniform(-variation, variation)
    
    def _fake_salary_prediction_model(self, 
                                     job_title: str,
                                     position: Optional[str] = None, 
                                     experience_level: Optional[str] = None,
                                     skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fake model to predict salary range using historical data and weights"""
        recent_data = self._get_recent_data(6)
        
        # Filter by job title
        job_data = recent_data[recent_data['job_title'].str.contains(job_title, case=False, na=False)]
        
        if position:
            # Also filter by position if provided
            position_data = recent_data[recent_data['position'].str.contains(position, case=False, na=False)]
            # Combine both datasets with higher weight to job_title matches
            job_data = pd.concat([job_data, position_data]).drop_duplicates()
        
        if job_data.empty:
            # If no matching jobs, use random values within a reasonable range
            min_salary = self._add_random_variation(2000, 0.2)
            max_salary = self._add_random_variation(4000, 0.2)
            confidence = 0.5
        else:
            # Base prediction on matching job data
            base_min = job_data['salary_min'].mean()
            base_max = job_data['salary_max'].mean()
            
            # Apply experience factor
            exp_factor = 1.0
            if experience_level:
                exp_factor = self._calculate_experience_factor(experience_level)
            
            # Apply skills factor
            skills_factor = 1.0
            if skills:
                skills_factor = self._calculate_skills_factor(skills, job_data)
            
            # Market trend factor (fake)
            market_trend = random.uniform(0.95, 1.05)
            
            # Calculate weighted prediction
            min_salary = base_min * (
                self.salary_weights['job_title'] +
                self.salary_weights['position'] * exp_factor +
                self.salary_weights['skills_match'] * skills_factor +
                self.salary_weights['market_trend'] * market_trend
            )
            
            max_salary = base_max * (
                self.salary_weights['job_title'] +
                self.salary_weights['position'] * exp_factor +
                self.salary_weights['skills_match'] * skills_factor +
                self.salary_weights['market_trend'] * market_trend
            )
            
            # Add random variation
            min_salary = self._add_random_variation(min_salary, 0.1)
            max_salary = self._add_random_variation(max_salary, 0.1)
            
            # Ensure max is greater than min
            if min_salary > max_salary:
                min_salary, max_salary = max_salary, min_salary
                
            # Calculate confidence based on amount of data
            confidence = min(0.95, 0.6 + 0.05 * len(job_data))
        
        # Determine trend (fake)
        trend_options = ["increasing", "stable", "decreasing"]
        trend_weights = [0.4, 0.4, 0.2]  # Biased toward positive or stable
        trend = random.choices(trend_options, weights=trend_weights, k=1)[0]
        
        avg_salary = (min_salary + max_salary) / 2
        
        return {
            "min_salary": round(min_salary, 2),
            "max_salary": round(max_salary, 2),
            "avg_salary": round(avg_salary, 2),
            "trend": trend,
            "confidence": round(confidence, 2)
        }
    
    async def _fake_job_postings_prediction_model(self,
                                               job_title: str,
                                               skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fake model to predict job postings for the next week"""
        recent_data = self._get_recent_data(6)
        
        # Filter by job title
        job_data = recent_data[recent_data['job_title'].str.contains(job_title, case=False, na=False)]
        
        if job_data.empty:
            # If no matching jobs, generate random prediction
            total_openings = random.randint(20, 50)  # Tổng số vị trí tuyển dụng
            confidence = 0.5
        else:
            # Tính tổng số vị trí tuyển dụng từ dữ liệu lịch sử
            if 'number_of_openings' in job_data.columns:
                total_openings = job_data['number_of_openings'].sum() / 26
            else:
                # Nếu không có dữ liệu, ước tính dựa trên số bài đăng
                total_openings = len(job_data) * random.uniform(2, 4)
            
            # Skills demand factor
            skills_factor = 1.0
            if skills:
                skills_factor = self._calculate_skills_factor(skills, job_data)
            
            # Market growth factor (fake)
            market_growth = random.uniform(0.9, 1.2)
            
            # Seasonality factor (fake) - adjust based on current month
            current_month = datetime.now().month
            seasonality = 1.0 + 0.1 * (current_month in [1, 6, 9])
            
            # Calculate weighted prediction
            total_openings = total_openings * (
                self.postings_weights['job_title'] +
                self.postings_weights['skills_demand'] * skills_factor +
                self.postings_weights['market_growth'] * market_growth +
                self.postings_weights['seasonality'] * seasonality
            )
            
            # Add random variation
            total_openings = self._add_random_variation(total_openings, 0.15)
            
            # Ensure reasonable openings
            total_openings = max(1, total_openings)
            
            # Calculate confidence based on amount of data
            confidence = min(0.95, 0.6 + 0.05 * len(job_data))
        
        # Determine trend (fake)
        trend_options = ["increasing", "stable", "decreasing"]
        trend_weights = [0.4, 0.4, 0.2]  # Biased toward positive or stable
        trend = random.choices(trend_options, weights=trend_weights, k=1)[0]
        
        return {
            "total_openings": round(total_openings),
            "trend": trend,
            "confidence": round(confidence, 2),
            "average_openings_per_posting": round(total_openings / len(job_data), 2) if len(job_data) > 0 else 0
        }
    
    async def predict_job_market(self,
                          job_title: str,
                          position: Optional[str] = None,
                          experience_level: Optional[str] = None,
                          skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate predictions for job salary and postings"""
        try:
            # Load data nếu chưa có
            if self.data is None:
                self.data = await self._load_data()
            
            # Get salary prediction
            salary_prediction = self._fake_salary_prediction_model(
                job_title=job_title,
                position=position,
                experience_level=experience_level,
                skills=skills
            )
            
            # Get job postings prediction
            job_postings_prediction = await self._fake_job_postings_prediction_model(
                job_title=job_title,
                skills=skills
            )
            
            return {
                "status": "success",
                "prediction_date": datetime.now(),
                "job_title": job_title,
                "salary_prediction": salary_prediction,
                "job_postings_prediction": job_postings_prediction
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "prediction_date": datetime.now(),
                "job_title": job_title
            }

    async def _get_popular_job_titles(self, limit: int = 10) -> List[str]:
        try:
            cutoff_date = datetime.now() - timedelta(days=30 * 6)
            job_postings = await JobPostingModel.find_by_date_range(cutoff_date, datetime.now())
            
            if not job_postings:
                logger.warning("Không tìm thấy dữ liệu job postings trong MongoDB")
                await self._save_error_log(
                    error_type="DataNotFound",
                    error_message="Không tìm thấy dữ liệu job postings trong MongoDB",
                    source="get_popular_job_titles",
                    additional_data={"limit": limit}
                )
                return ["Data Scientist", "Software Engineer", "Frontend Developer", 
                        "Backend Developer", "DevOps Engineer"]
            
            # ... rest of the code ...
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy job titles phổ biến từ MongoDB: {e}")
            await self._save_error_log(
                error_type="DatabaseError",
                error_message=str(e),
                source="get_popular_job_titles",
                stack_trace=str(e.__traceback__),
                additional_data={"limit": limit}
            )
            return ["Data Scientist", "Software Engineer", "Frontend Developer", 
                    "Backend Developer", "DevOps Engineer"]

    async def _save_to_mongodb(self, predictions: Dict[str, Any]):
        try:
            for job_title, prediction in predictions.items():
                career_history_data = {
                    "job_title": job_title,
                    "status": prediction["status"],
                    "prediction_date": datetime.strptime(prediction["prediction_date"], "%Y-%m-%d %H:%M:%S") 
                        if isinstance(prediction["prediction_date"], str) else prediction["prediction_date"],
                    "salary_prediction": prediction["salary_prediction"],
                    "job_postings_prediction": prediction["job_postings_prediction"]
                }
                
                await CareerHistoryModel.create(career_history_data)
                
            logger.info("Đã lưu kết quả dự đoán vào MongoDB")
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả dự đoán vào MongoDB: {e}")
            await self._save_error_log(
                error_type="DatabaseError",
                error_message=str(e),
                source="save_to_mongodb",
                stack_trace=str(e.__traceback__),
                additional_data={"predictions_count": len(predictions)}
            )

    async def _run_daily_predictions(self):
        logger.info(f"Đang chạy dự đoán hàng ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            job_titles = await self._get_popular_job_titles()
            date_str = datetime.now().strftime('%Y-%m-%d')
            file_path = self.predictions_dir / f"predictions_{date_str}.json"
            
            predictions = {}
            for job_title in job_titles:
                try:
                    prediction = await self.predict_job_market(
                        job_title=job_title
                    )
                    
                    if isinstance(prediction.get('prediction_date'), datetime):
                        prediction['prediction_date'] = prediction['prediction_date'].strftime('%Y-%m-%d %H:%M:%S')
                        
                    predictions[job_title] = prediction
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
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(predictions, f, ensure_ascii=False, indent=2)
                logger.info(f"Đã lưu kết quả dự đoán vào file: {file_path}")
            except Exception as e:
                logger.error(f"Lỗi khi lưu kết quả dự đoán vào file: {e}")
                await self._save_error_log(
                    error_type="FileError",
                    error_message=str(e),
                    source="run_daily_predictions",
                    stack_trace=str(e.__traceback__),
                    additional_data={"file_path": str(file_path)}
                )
            
            await self._save_to_mongodb(predictions)
            
        except Exception as e:
            logger.error(f"Lỗi khi chạy dự đoán hàng ngày: {e}")
            await self._save_error_log(
                error_type="SystemError",
                error_message=str(e),
                source="run_daily_predictions",
                stack_trace=str(e.__traceback__)
            )

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