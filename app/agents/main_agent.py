from typing import Dict, Any
import logging
from app.agents.sub_agents import CodeSummarizer, DiffAnalyzer, CodeTypeClassifier
from app.agents.review_generator import ReviewGenerator
from app.agents.feedback_analyzer import feedback_analyzer, prompt_updater
from app.agents.dynamic_prompts import dynamic_prompt_manager
from app.database import get_db, PRReview, Feedback
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class MainAgent:
    """Main LLM Orchestrator that coordinates all sub-agents"""
    
    def __init__(self):
        self.code_summarizer = CodeSummarizer()
        self.diff_analyzer = DiffAnalyzer()
        self.code_classifier = CodeTypeClassifier()
        self.review_generator = ReviewGenerator()
    
    async def process_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestrator method that processes a PR through all agents
        """
        logger.info(f"Processing PR #{pr_data.get('number')} from {pr_data.get('repository')}")
        
        try:
            # Extract PR information
            pr_number = pr_data.get('number')
            repo_name = pr_data.get('repository')
            pr_title = pr_data.get('title', '')
            pr_description = pr_data.get('description', '')
            diff_content = pr_data.get('diff', '')
            file_list = pr_data.get('files', [])
            
            # Step 1: Summarize code changes
            logger.info("Running code summarizer...")
            summary = await self.code_summarizer.summarize_changes(
                diff_content, pr_title, pr_description
            )
            
            # Step 2: Analyze diff with context
            logger.info("Running diff analyzer...")
            analysis = await self.diff_analyzer.analyze_diff(diff_content, file_list)
            
            # Step 3: Classify code type
            logger.info("Running code type classifier...")
            code_type = await self.code_classifier.classify_code_type(diff_content, file_list)
            
            # Step 4: Generate review based on type
            logger.info(f"Generating review for {code_type} code...")
            review = await self.review_generator.generate_review(
                code_type, summary, analysis, diff_content
            )
            
            # Step 5: Store in database
            review_data = {
                'pr_number': pr_number,
                'repo_full_name': repo_name,
                'review_content': review,
                'code_type': code_type,
                'summary': summary,
                'diff_analysis': analysis,
                'metadata': {
                    'pr_title': pr_title,
                    'pr_description': pr_description,
                    'files_changed': len(file_list),
                    'files': file_list[:10]  # Store first 10 files
                }
            }
            
            # Save to database
            self._save_review_to_db(review_data)
            
            logger.info(f"Successfully processed PR #{pr_number}")
            
            return {
                'success': True,
                'pr_number': pr_number,
                'repo_name': repo_name,
                'code_type': code_type,
                'review': review,
                'summary': summary,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error processing PR: {e}")
            return {
                'success': False,
                'error': str(e),
                'pr_number': pr_data.get('number'),
                'repo_name': pr_data.get('repository')
            }
    
    def _save_review_to_db(self, review_data: Dict[str, Any]):
        """Save review to database"""
        try:
            db = next(get_db())
            review = PRReview(**review_data)
            db.add(review)
            db.commit()
            db.refresh(review)
            logger.info(f"Saved review to database with ID: {review.id}")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def process_feedback(self, review_id: int, feedback_content: str) -> Dict[str, Any]:
        """
        Process feedback and update the system to improve future reviews
        """
        logger.info(f"Processing feedback for review ID: {review_id}")
        
        try:
            # Get the original review from database
            db = next(get_db())
            review = db.query(PRReview).filter(PRReview.id == review_id).first()
            
            if not review:
                return {'success': False, 'error': 'Review not found'}
            
            # Analyze the feedback
            feedback_analysis = await feedback_analyzer.analyze_feedback(
                feedback_content=feedback_content,
                original_review=review.review_content,
                code_type=review.code_type
            )
            
            logger.info(f"Feedback analysis: {feedback_analysis.get('feedback_type')} priority: {feedback_analysis.get('priority')}")
            
            # Store the feedback in database
            new_feedback = Feedback(
                review_id=review_id,
                feedback_type=feedback_analysis.get('feedback_type', 'unknown'),
                feedback_content=feedback_content
            )
            db.add(new_feedback)
            
            # If feedback suggests improvements, update prompts
            if feedback_analysis.get('priority') in ['high', 'medium'] and feedback_analysis.get('prompt_updates'):
                current_prompt = dynamic_prompt_manager.get_prompt(review.code_type)
                
                # Update the prompt based on feedback
                updated_prompt = await prompt_updater.update_prompt(
                    code_type=review.code_type,
                    current_prompt=current_prompt,
                    feedback_analysis=feedback_analysis
                )
                
                # Save the updated prompt
                feedback_summary = f"Areas: {', '.join(feedback_analysis.get('improvement_areas', []))}"
                dynamic_prompt_manager.update_prompt(
                    code_type=review.code_type,
                    new_prompt=updated_prompt,
                    feedback_summary=feedback_summary
                )
                
                logger.info(f"Updated {review.code_type} prompt based on feedback")
            
            db.commit()
            
            return {
                'success': True,
                'feedback_analysis': feedback_analysis,
                'prompt_updated': feedback_analysis.get('priority') in ['high', 'medium'],
                'review_id': review_id
            }
            
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            if 'db' in locals():
                db.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            if 'db' in locals():
                db.close()

main_agent = MainAgent()