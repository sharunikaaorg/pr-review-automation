import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./pr_reviews.db")
    
    # Groq settings
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # GitHub API settings
    GITHUB_API_URL: str = "https://api.github.com"

settings = Settings()