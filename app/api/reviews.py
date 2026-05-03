from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db, PRReview, Feedback
from app.agents.main_agent import main_agent
from app.agents.dynamic_prompts import dynamic_prompt_manager
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class FeedbackCreate(BaseModel):
    review_id: int
    feedback_type: str
    feedback_content: str

class ReviewResponse(BaseModel):
    id: int
    pr_number: int
    repo_full_name: str
    code_type: str
    review_content: str
    summary: str
    created_at: str
    
    class Config:
        from_attributes = True

@router.get("/reviews", response_model=List[ReviewResponse])
async def get_reviews(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """Get list of PR reviews"""
    reviews = db.query(PRReview).offset(skip).limit(limit).all()
    return reviews

@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get specific review by ID"""
    review = db.query(PRReview).filter(PRReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.post("/reviews/{review_id}/feedback")
async def add_feedback(review_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Add feedback to a review"""
    # Check if review exists
    review = db.query(PRReview).filter(PRReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Create feedback
    new_feedback = Feedback(
        review_id=review_id,
        feedback_type=feedback.feedback_type,
        feedback_content=feedback.feedback_content
    )
    
    db.add(new_feedback)
    db.commit()
    
    return {"message": "Feedback added successfully"}

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get basic statistics"""
    total_reviews = db.query(PRReview).count()
    frontend_reviews = db.query(PRReview).filter(PRReview.code_type == 'frontend').count()
    backend_reviews = db.query(PRReview).filter(PRReview.code_type == 'backend').count()
    other_reviews = db.query(PRReview).filter(PRReview.code_type == 'other').count()
    
    return {
        "total_reviews": total_reviews,
        "frontend_reviews": frontend_reviews,
        "backend_reviews": backend_reviews,
        "other_reviews": other_reviews
    }

@router.post("/reviews/{review_id}/process-feedback")
async def process_review_feedback(review_id: int, feedback_content: str, db: Session = Depends(get_db)):
    """Process feedback for a specific review and update the system"""
    
    # Check if review exists
    review = db.query(PRReview).filter(PRReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    try:
        result = await main_agent.process_feedback(review_id, feedback_content)
        return result
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prompts")
async def get_all_prompts():
    """Get current prompts for all code types"""
    return {
        "frontend": dynamic_prompt_manager.get_prompt_info("frontend"),
        "backend": dynamic_prompt_manager.get_prompt_info("backend"),
        "other": dynamic_prompt_manager.get_prompt_info("other")
    }

@router.get("/prompts/{code_type}")
async def get_prompt(code_type: str):
    """Get current prompt for specific code type"""
    if code_type not in ["frontend", "backend", "other"]:
        raise HTTPException(status_code=400, detail="Invalid code type")
    
    return dynamic_prompt_manager.get_prompt_info(code_type)

@router.post("/prompts/reset")
async def reset_prompts():
    """Reset all prompts to defaults"""
    dynamic_prompt_manager.reset_prompts()
    return {"message": "All prompts reset to defaults"}

@router.get("/feedback-stats")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics"""
    total_feedback = db.query(Feedback).count()
    positive_feedback = db.query(Feedback).filter(Feedback.feedback_type == 'positive').count()
    negative_feedback = db.query(Feedback).filter(Feedback.feedback_type == 'negative').count()
    suggestion_feedback = db.query(Feedback).filter(Feedback.feedback_type == 'suggestion').count()
    
    return {
        "total_feedback": total_feedback,
        "positive_feedback": positive_feedback,
        "negative_feedback": negative_feedback,
        "suggestion_feedback": suggestion_feedback,
        "feedback_types": {
            "positive": positive_feedback,
            "negative": negative_feedback,
            "suggestion": suggestion_feedback,
            "clarification": total_feedback - (positive_feedback + negative_feedback + suggestion_feedback)
        }
    }