from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from typing import Dict, Any
import json
import logging
from app.github.client import github_client
from app.agents.main_agent import main_agent

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/github/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    
    # Get headers and payload
    signature = request.headers.get('X-Hub-Signature-256', '')
    event_type = request.headers.get('X-GitHub-Event', '')
    
    # Read raw payload
    payload_bytes = await request.body()
    
    # Verify webhook signature
    if not github_client.verify_webhook_signature(payload_bytes, signature):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.info(f"Received {event_type} webhook event")
    
    # Handle pull request events
    if event_type == "pull_request":
        await handle_pull_request_event(payload, background_tasks)
    elif event_type == "issue_comment":
        await handle_comment_event(payload, background_tasks)
    else:
        logger.info(f"Ignoring {event_type} event")
    
    return {"message": "Webhook received successfully"}

async def handle_pull_request_event(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle pull request webhook events"""
    
    action = payload.get('action')
    
    # We're interested in opened, reopened, and synchronize (new commits) events
    if action in ['opened', 'reopened', 'synchronize']:
        pr = payload.get('pull_request', {})
        repo = payload.get('repository', {})
        
        pr_number = pr.get('number')
        repo_full_name = repo.get('full_name')
        
        if not pr_number or not repo_full_name:
            logger.error("Missing PR number or repository name")
            return
        
        logger.info(f"Processing PR #{pr_number} in {repo_full_name} (action: {action})")
        
        # Process the PR in the background
        background_tasks.add_task(process_pr_async, repo_full_name, pr_number)
    else:
        logger.info(f"Ignoring PR action: {action}")

async def process_pr_async(repo_full_name: str, pr_number: int):
    """Process PR asynchronously in the background"""
    try:
        # Fetch detailed PR data from GitHub
        logger.info(f"Fetching PR data for #{pr_number}")
        pr_data = await github_client.get_pr_data(repo_full_name, pr_number)
        
        # Process through main agent
        logger.info(f"Processing PR #{pr_number} through main agent")
        result = await main_agent.process_pr(pr_data)
        
        if result.get('success'):
            # Post review back to GitHub
            logger.info(f"Posting review to PR #{pr_number}")
            success = await github_client.post_review(
                repo_full_name, 
                pr_number, 
                result.get('review', '')
            )
            
            if success:
                logger.info(f"Successfully completed processing PR #{pr_number}")
            else:
                logger.error(f"Failed to post review for PR #{pr_number}")
        else:
            logger.error(f"Failed to process PR #{pr_number}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in async PR processing: {e}")

async def handle_comment_event(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle issue/PR comment events to capture feedback"""
    
    action = payload.get('action')
    
    # Only process new comments
    if action != 'created':
        return
    
    comment = payload.get('comment', {})
    issue = payload.get('issue', {})
    
    # Check if this is a PR comment (issues and PRs share the same API)
    if not issue.get('pull_request'):
        return
    
    comment_body = comment.get('body', '').strip()
    comment_author = comment.get('user', {}).get('login', '')
    pr_number = issue.get('number')
    repo_full_name = payload.get('repository', {}).get('full_name')
    
    logger.info(f"Processing comment on PR #{pr_number} by {comment_author}")
    
    # Look for feedback indicators in the comment
    feedback_indicators = [
        '@pr-bot', 'feedback:', 'review feedback:', 
        'bot feedback:', 'improve:', 'suggestion:',
        'the review should', 'missing from review',
        'review missed', 'add to review'
    ]
    
    # Check if this looks like feedback for our bot
    is_feedback = any(indicator in comment_body.lower() for indicator in feedback_indicators)
    
    if is_feedback:
        logger.info(f"Detected feedback comment from {comment_author}")
        background_tasks.add_task(process_feedback_comment, repo_full_name, pr_number, comment_body, comment_author)

async def process_feedback_comment(repo_full_name: str, pr_number: int, feedback_content: str, feedback_author: str):
    """Process feedback comment and improve the system"""
    try:
        from app.database import get_db, PRReview
        
        # Find the most recent review for this PR
        db = next(get_db())
        review = db.query(PRReview)\
            .filter(PRReview.repo_full_name == repo_full_name)\
            .filter(PRReview.pr_number == pr_number)\
            .order_by(PRReview.created_at.desc())\
            .first()
        
        if not review:
            logger.warning(f"No review found for PR #{pr_number} in {repo_full_name}")
            return
        
        # Process the feedback through main agent
        logger.info(f"Processing feedback for review ID {review.id}")
        result = await main_agent.process_feedback(review.id, feedback_content)
        
        if result.get('success'):
            logger.info(f"Successfully processed feedback from {feedback_author}")
            
            # Optionally post a response comment acknowledging the feedback
            try:
                feedback_type = result.get('feedback_analysis', {}).get('feedback_type', 'unknown')
                prompt_updated = result.get('prompt_updated', False)
                
                response_message = f"Thank you @{feedback_author} for the feedback! "
                if prompt_updated:
                    response_message += "I've updated my review approach based on your suggestions. 🤖✨"
                else:
                    response_message += "I've noted your feedback for future improvements. 🤖📝"
                
                await github_client.post_review(repo_full_name, pr_number, response_message)
                
            except Exception as e:
                logger.error(f"Error posting feedback acknowledgment: {e}")
                
        else:
            logger.error(f"Failed to process feedback: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error in feedback processing: {e}")
    finally:
        if 'db' in locals():
            db.close()