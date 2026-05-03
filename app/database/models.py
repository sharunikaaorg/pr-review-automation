from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class PRReview(Base):
    __tablename__ = "pr_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    pr_number = Column(Integer, nullable=False)
    repo_full_name = Column(String(255), nullable=False)
    review_content = Column(Text, nullable=False)
    code_type = Column(String(50), nullable=False)  # frontend, backend, other
    summary = Column(Text, nullable=True)
    diff_analysis = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Store additional metadata
    pr_metadata = Column("metadata", JSON, nullable=True)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False)
    feedback_type = Column(String(50), nullable=False)  # positive, negative, suggestion
    feedback_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())