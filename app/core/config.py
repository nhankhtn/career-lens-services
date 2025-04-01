import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Data settings
DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "IT_jobs_postings.csv") 