from typing import Dict, Any
from app.agents.groq_client import groq_client
from app.agents.dynamic_prompts import dynamic_prompt_manager
import logging

logger = logging.getLogger(__name__)

class ReviewGenerator:
    """Generates PR reviews based on code type and analysis"""
    
    @staticmethod
    async def generate_review(
        code_type: str,
        summary: str,
        analysis: str,
        diff_content: str
    ) -> str:
        """Generate a comprehensive PR review using dynamic prompts"""
        
        # Get the current dynamic prompt for the code type
        prompt_template = dynamic_prompt_manager.get_prompt(code_type)
        
        # Format the prompt with actual data
        prompt = prompt_template.format(
            summary=summary,
            analysis=analysis,
            diff_content=diff_content[:5000]  # Limit diff content to avoid token limits
        )
        
        try:
            review = await groq_client.generate_response(prompt, max_tokens=1500)
            return review
        except Exception as e:
            logger.error(f"Error generating review: {e}")
            return f"Error generating review for {code_type} code: {str(e)}"