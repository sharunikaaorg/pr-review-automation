from typing import Dict, Any
from app.agents.groq_client import groq_client
import logging

logger = logging.getLogger(__name__)

class CodeSummarizer:
    """Sub-agent responsible for summarizing code changes"""
    
    @staticmethod
    async def summarize_changes(diff_content: str, pr_title: str, pr_description: str) -> str:
        prompt = f"""
        You are a code summarizer. Please provide a concise summary of the code changes in this pull request.

        PR Title: {pr_title}
        PR Description: {pr_description}

        Diff Content:
        {diff_content[:3000]}  # Limit diff to avoid token limits

        Please provide:
        1. A brief overview of what was changed
        2. Key files modified
        3. Main functionality added/modified/removed

        Keep the summary under 200 words.
        """
        
        try:
            return await groq_client.generate_response(prompt, max_tokens=300)
        except Exception as e:
            logger.error(f"Error in code summarizer: {e}")
            return "Error generating code summary"

class DiffAnalyzer:
    """Sub-agent responsible for analyzing diffs with context"""
    
    @staticmethod
    async def analyze_diff(diff_content: str, file_list: list) -> str:
        prompt = f"""
        You are a diff analyzer. Analyze the following code diff and provide insights about:

        Files changed: {', '.join(file_list[:10])}  # Show first 10 files

        Diff Content:
        {diff_content[:4000]}  # Limit diff to avoid token limits

        Please analyze:
        1. Complexity of changes (low/medium/high)
        2. Potential risk areas
        3. Areas that might need special attention during review
        4. Code quality observations
        5. Any obvious issues or concerns

        Provide a structured analysis.
        """
        
        try:
            return await groq_client.generate_response(prompt, max_tokens=500)
        except Exception as e:
            logger.error(f"Error in diff analyzer: {e}")
            return "Error analyzing diff"

class CodeTypeClassifier:
    """Sub-agent responsible for classifying code type"""
    
    @staticmethod
    async def classify_code_type(diff_content: str, file_list: list) -> str:
        # Simple classification based on file extensions
        frontend_extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css', '.scss', '.sass'}
        backend_extensions = {'.py', '.java', '.go', '.rb', '.php', '.rs', '.cpp', '.c', '.cs'}
        
        frontend_files = sum(1 for file in file_list if any(file.endswith(ext) for ext in frontend_extensions))
        backend_files = sum(1 for file in file_list if any(file.endswith(ext) for ext in backend_extensions))
        
        # If we have a clear majority, return that
        if frontend_files > backend_files * 2:
            return "frontend"
        elif backend_files > frontend_files * 2:
            return "backend"
        
        # For ambiguous cases, use LLM classification
        prompt = f"""
        You are a code type classifier. Based on the files changed and diff content, classify this PR as one of:
        - frontend (UI, client-side, web interface changes)
        - backend (server-side, API, database, business logic changes)
        - other (infrastructure, config, documentation, mixed changes)

        Files changed: {', '.join(file_list[:15])}

        Diff sample:
        {diff_content[:2000]}

        Respond with only one word: frontend, backend, or other
        """
        
        try:
            result = await groq_client.generate_response(prompt, max_tokens=50)
            classification = result.strip().lower()
            if classification in ['frontend', 'backend', 'other']:
                return classification
            return 'other'
        except Exception as e:
            logger.error(f"Error in code type classifier: {e}")
            return 'other'