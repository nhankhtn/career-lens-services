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

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "SJyVxheQr0g10zyjZV01BmsCojvm7vkJkp9THFnrBg0=")
JWT_EXPIRE_IN = os.getenv("JWT_EXPIRE_IN", "100d")

# Data settings
DATA_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "IT_jobs_postings.csv") 