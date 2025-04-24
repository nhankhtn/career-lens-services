from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import career_guidance, job_prediction, scheduler

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
app.include_router(job_prediction.router)
app.include_router(scheduler.router)

@app.get("/")
async def root():
    # print(f"Connected to database: {db_name}")
    return {"message": "Welcome to the IT Career Guidance & Job Market Prediction API"} 