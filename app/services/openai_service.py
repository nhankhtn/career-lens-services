import openai
from app.core.config import OPENAI_API_KEY
import pandas as pd
import json

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

class OpenAIService:
    def __init__(self, jobs_data_path):
        """Initialize OpenAI service with jobs data"""
        self.jobs_df = pd.read_csv(jobs_data_path)
        
    def generate_career_guidance(self, education, skills, experience, certificates, target_job):
        """
        Generate career guidance based on user profile and target job using OpenAI
        
        Args:
            education: User's education background
            skills: User's current skills
            experience: User's work experience
            certificates: User's certificates
            target_job: User's target job
            
        Returns:
            dict: Career guidance response
        """
        # Convert jobs dataframe to a list of job dictionaries
        jobs_data = self.jobs_df.to_dict(orient='records')
        
        # Find relevant job postings
        relevant_jobs = []
        for job in jobs_data:
            if target_job.lower() in job['Job Title'].lower():
                relevant_jobs.append(job)
        
        # If no exact matches, include jobs that might be related
        if not relevant_jobs:
            for job in jobs_data:
                if any(keyword in job['Job Title'].lower() for keyword in target_job.lower().split()):
                    relevant_jobs.append(job)
        
        # Prepare user profile
        user_profile = {
            "education": education,
            "skills": skills,
            "experience": experience,
            "certificates": certificates,
            "target_job": target_job
        }
        
        # Prepare the system prompt with job data
        system_prompt = f"""
        You are a career advisor specialized in IT and data roles. You'll provide personalized career guidance.
        
        Available IT job postings:
        {json.dumps(relevant_jobs, indent=2)}
        
        Based on the user's profile and the job requirements, provide:
        1. Gap analysis: What skills, experience, or education they need to acquire
        2. Learning path: Recommended courses, certifications, or experiences
        3. Timeline: Realistic timeline to transition to their target role
        4. Alternative paths: Similar roles they could consider as stepping stones
        
        Be specific and actionable in your advice.
        """
        
        # Prepare the user prompt with the profile
        user_prompt = f"""
        Here's my profile:
        - Education: {education}
        - Skills: {skills}
        - Experience: {experience}
        - Certificates: {certificates}
        - Target job: {target_job}
        
        Please provide career guidance to help me reach my target job.
        """
        
        try:
            # Call the OpenAI API
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract and return the response
            guidance = response.choices[0].message.content
            
            return {
                "status": "success",
                "guidance": guidance,
                "relevant_jobs_count": len(relevant_jobs)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            } 