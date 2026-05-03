from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.database import create_tables
from app.api.webhooks import router as webhook_router
from app.api.reviews import router as reviews_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PR Review Automation System",
    description="Automated PR review system using LLM agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(webhook_router, prefix="/api/v1")
app.include_router(reviews_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database and other startup tasks"""
    logger.info("Starting PR Review Automation System...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Verify configuration
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not configured - LLM features will not work")
    
    if not settings.GITHUB_TOKEN:
        logger.warning("GITHUB_TOKEN not configured - GitHub integration will not work")
    
    logger.info("System startup complete")

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "PR Review Automation System",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/api/v1/github/webhook",
            "reviews": "/api/v1/reviews",
            "stats": "/api/v1/stats",
            "prompts": "/api/v1/prompts",
            "feedback": "/api/v1/reviews/{id}/process-feedback",
            "feedback_stats": "/api/v1/feedback-stats"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "groq_configured": bool(settings.GROQ_API_KEY),
        "github_configured": bool(settings.GITHUB_TOKEN)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)