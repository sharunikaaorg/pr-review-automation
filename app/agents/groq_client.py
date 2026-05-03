from groq import Groq
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
    
    async def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate response using Groq API"""
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=settings.GROQ_MODEL,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from Groq: {e}")
            raise e

groq_client = GroqClient()