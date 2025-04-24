import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# X settings
X_API_KEY = os.getenv("X_API_KEY")
if not X_API_KEY:
    raise ValueError("X_API_KEY environment variable is not set")


# Data settings
DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "IT_jobs_postings.csv") 