import requests
from github import Github
from typing import Dict, Any, List
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GitHubClient:
    """GitHub API client for fetching PR data and posting reviews"""
    
    def __init__(self):
        self.github = Github(settings.GITHUB_TOKEN)
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {settings.GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    async def get_pr_data(self, repo_full_name: str, pr_number: int) -> Dict[str, Any]:
        """Fetch comprehensive PR data from GitHub"""
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Get PR diff
            diff_response = self.session.get(
                f"{settings.GITHUB_API_URL}/repos/{repo_full_name}/pulls/{pr_number}",
                headers={'Accept': 'application/vnd.github.v3.diff'}
            )
            diff_content = diff_response.text if diff_response.status_code == 200 else ""
            
            # Get list of changed files
            files = pr.get_files()
            file_list = [f.filename for f in files]
            
            return {
                'number': pr_number,
                'repository': repo_full_name,
                'title': pr.title,
                'description': pr.body or '',
                'diff': diff_content,
                'files': file_list,
                'author': pr.user.login,
                'base_branch': pr.base.ref,
                'head_branch': pr.head.ref,
                'url': pr.html_url
            }
            
        except Exception as e:
            logger.error(f"Error fetching PR data: {e}")
            raise e
    
    async def post_review(self, repo_full_name: str, pr_number: int, review_content: str) -> bool:
        """Post review as a comment on the PR"""
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            # Post the review as a comment
            comment_body = f"## 🤖 Automated Code Review\n\n{review_content}"
            pr.create_issue_comment(comment_body)
            
            logger.info(f"Successfully posted review to PR #{pr_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error posting review: {e}")
            return False
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        if not settings.WEBHOOK_SECRET:
            logger.warning("No webhook secret configured - skipping signature verification")
            return True
        
        import hmac
        import hashlib
        
        expected_signature = 'sha256=' + hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

github_client = GitHubClient()