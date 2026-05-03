from typing import Dict, Any, List
from app.agents.groq_client import groq_client
import logging

logger = logging.getLogger(__name__)

class FeedbackAnalyzer:
    """Analyzes feedback and determines improvement actions"""
    
    @staticmethod
    async def analyze_feedback(feedback_content: str, original_review: str, code_type: str) -> Dict[str, Any]:
        """
        Analyze feedback and determine what improvements to make
        """
        prompt = f"""
        You are a feedback analyzer for an automated code review system. 
        
        ORIGINAL REVIEW:
        {original_review}
        
        CODE TYPE: {code_type}
        
        FEEDBACK RECEIVED:
        {feedback_content}
        
        Please analyze this feedback and provide:
        
        1. FEEDBACK_TYPE: One of the following:
           - "positive" - Good review, reinforce this approach
           - "negative" - Poor review, needs significant improvement
           - "suggestion" - Constructive feedback with specific improvements
           - "clarification" - Request for more details or explanation
        
        2. IMPROVEMENT_AREAS: List specific areas that need improvement (e.g., "security analysis", "performance considerations", "code style", "testing suggestions")
        
        3. SPECIFIC_ISSUES: Extract specific problems mentioned in the feedback
        
        4. SUGGESTED_CHANGES: What changes should be made to improve future reviews
        
        5. PROMPT_UPDATES: Specific additions or modifications to make to the {code_type} prompt
        
        Format your response as JSON:
        {{
            "feedback_type": "suggestion",
            "confidence": 0.8,
            "improvement_areas": ["security", "testing"],
            "specific_issues": ["Missing input validation", "No test coverage mentioned"],
            "suggested_changes": ["Add more focus on security vulnerabilities", "Always mention testing requirements"],
            "prompt_updates": ["Add specific section about input validation", "Include testing coverage requirements"],
            "priority": "high"
        }}
        """
        
        try:
            response = await groq_client.generate_response(prompt, max_tokens=800)
            # Try to parse as JSON, fallback to text analysis if it fails
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback: extract key information manually
                return {
                    "feedback_type": "suggestion",
                    "confidence": 0.5,
                    "improvement_areas": ["general"],
                    "specific_issues": [feedback_content[:200]],
                    "suggested_changes": ["Review feedback and improve"],
                    "prompt_updates": ["Consider feedback: " + feedback_content[:100]],
                    "priority": "medium",
                    "raw_analysis": response
                }
        except Exception as e:
            logger.error(f"Error analyzing feedback: {e}")
            return {
                "feedback_type": "unknown",
                "confidence": 0.0,
                "improvement_areas": [],
                "specific_issues": [str(e)],
                "suggested_changes": [],
                "prompt_updates": [],
                "priority": "low",
                "error": str(e)
            }

class PromptUpdater:
    """Updates prompts based on feedback analysis"""
    
    @staticmethod
    async def update_prompt(code_type: str, current_prompt: str, feedback_analysis: Dict[str, Any]) -> str:
        """
        Update prompt based on feedback analysis
        """
        prompt_updates = feedback_analysis.get('prompt_updates', [])
        improvement_areas = feedback_analysis.get('improvement_areas', [])
        priority = feedback_analysis.get('priority', 'medium')
        
        if not prompt_updates and not improvement_areas:
            return current_prompt
        
        update_prompt = f"""
        You are a prompt engineer. Update the following code review prompt to address the feedback received.
        
        CURRENT PROMPT:
        {current_prompt}
        
        FEEDBACK ANALYSIS:
        - Priority: {priority}
        - Areas to improve: {', '.join(improvement_areas)}
        - Specific updates needed: {', '.join(prompt_updates)}
        - Issues identified: {', '.join(feedback_analysis.get('specific_issues', []))}
        
        Please provide an improved version of the prompt that:
        1. Addresses the feedback concerns
        2. Maintains the original structure and intent
        3. Adds specific guidance for the identified improvement areas
        4. Is clear and actionable for the review agent
        
        Return ONLY the updated prompt text, no additional commentary.
        """
        
        try:
            updated_prompt = await groq_client.generate_response(update_prompt, max_tokens=1200)
            return updated_prompt.strip()
        except Exception as e:
            logger.error(f"Error updating prompt: {e}")
            return current_prompt

feedback_analyzer = FeedbackAnalyzer()
prompt_updater = PromptUpdater()