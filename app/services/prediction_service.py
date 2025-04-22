import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

class PredictionService:
    """Service to predict job salaries and postings using fake models with fake weights"""
    
    def __init__(self, data_file_path: str):
        """Initialize with data file path"""
        self.data_file_path = data_file_path
        self.data = self._load_data()
        # Fake model weights for salary prediction
        self.salary_weights = {
            'job_title': 0.4,
            'position': 0.3,
            'experience_level': 0.3,
            'skills_match': 0.2,
            'market_trend': 0.2,
            'random_factor': 0.1
        }
        
        # Fake model weights for job postings prediction
        self.postings_weights = {
            'job_title': 0.35,
            'skills_demand': 0.25,
            'market_growth': 0.2,
            'seasonality': 0.1,
            'random_factor': 0.1
        }
    
    def _load_data(self) -> pd.DataFrame:
        """Load job postings data from CSV file"""
        try:
            df = pd.read_csv(self.data_file_path)
            # Convert date_posted to datetime
            df['date_posted'] = pd.to_datetime(df['date_posted'])
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            # Return empty DataFrame with expected columns if file can't be loaded
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
    
    def _fake_job_postings_prediction_model(self,
                                           job_title: str,
                                           skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fake model to predict job postings for the next week"""
        recent_data = self._get_recent_data(6)
        
        # Filter by job title
        job_data = recent_data[recent_data['job_title'].str.contains(job_title, case=False, na=False)]
        
        if job_data.empty:
            # If no matching jobs, generate random prediction
            weekly_postings = random.randint(5, 15)
            confidence = 0.5
            top_companies = ["Company A", "Company B", "Company C", "Company D"]
        else:
            # Calculate base posting count based on historical data
            # In a real model, we'd analyze the frequency over time
            base_count = len(job_data) / 26  # Divide by 26 weeks (6 months)
            
            # Skills demand factor
            skills_factor = 1.0
            if skills:
                skills_factor = self._calculate_skills_factor(skills, job_data)
            
            # Market growth factor (fake)
            market_growth = random.uniform(0.9, 1.2)
            
            # Seasonality factor (fake) - adjust based on current month
            current_month = datetime.now().month
            # More jobs in January, June, and September
            seasonality = 1.0 + 0.1 * (current_month in [1, 6, 9])
            
            # Calculate weighted prediction
            weekly_postings = base_count * (
                self.postings_weights['job_title'] +
                self.postings_weights['skills_demand'] * skills_factor +
                self.postings_weights['market_growth'] * market_growth +
                self.postings_weights['seasonality'] * seasonality
            )
            
            # Add random variation
            weekly_postings = self._add_random_variation(weekly_postings, 0.15)
            
            # Ensure at least 1 posting per week
            weekly_postings = max(1, weekly_postings)
            
            # Calculate confidence based on amount of data
            confidence = min(0.95, 0.6 + 0.05 * len(job_data))
            
            # Extract top companies
            if 'company_id' in job_data.columns and not job_data['company_id'].empty:
                company_counts = job_data['company_id'].value_counts().head(4)
                top_companies = company_counts.index.tolist()
            else:
                top_companies = ["Google", "Amazon", "Microsoft", "VNG Corporation"]
        
        # Determine trend (fake)
        trend_options = ["increasing", "stable", "decreasing"]
        trend_weights = [0.4, 0.4, 0.2]  # Biased toward positive or stable
        trend = random.choices(trend_options, weights=trend_weights, k=1)[0]
        
        return {
            "weekly_postings": round(weekly_postings),
            "trend": trend,
            "confidence": round(confidence, 2),
            "top_companies": top_companies
        }
    
    def predict_job_market(self,
                          job_title: str,
                          position: Optional[str] = None,
                          experience_level: Optional[str] = None,
                          skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate predictions for job salary and postings"""
        try:
            # Get salary prediction
            salary_prediction = self._fake_salary_prediction_model(
                job_title=job_title,
                position=position,
                experience_level=experience_level,
                skills=skills
            )
            
            # Get job postings prediction
            job_postings_prediction = self._fake_job_postings_prediction_model(
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