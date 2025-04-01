from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import career_guidance

app = FastAPI(title="IT Career Guidance API", 
             description="API for IT career guidance based on user profile and job preferences")

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

@app.get("/")
async def root():
    return {"message": "Welcome to the IT Career Guidance API"} 