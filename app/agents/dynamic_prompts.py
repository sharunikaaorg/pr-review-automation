import json
import os
from typing import Dict, Any
from datetime import datetime
from app.agents.prompts import FRONTEND_PROMPT, BACKEND_PROMPT, GENERIC_PROMPT
import logging

logger = logging.getLogger(__name__)

class DynamicPromptManager:
    """Manages dynamic prompts that can be updated based on feedback"""
    
    def __init__(self):
        self.prompts_file = "dynamic_prompts.json"
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from file or initialize with defaults"""
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading prompts file: {e}")
        
        # Initialize with default prompts
        return {
            "frontend": {
                "prompt": FRONTEND_PROMPT,
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "updates_count": 0,
                "feedback_incorporated": []
            },
            "backend": {
                "prompt": BACKEND_PROMPT,
                "version": "1.0", 
                "last_updated": datetime.now().isoformat(),
                "updates_count": 0,
                "feedback_incorporated": []
            },
            "other": {
                "prompt": GENERIC_PROMPT,
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "updates_count": 0,
                "feedback_incorporated": []
            }
        }
    
    def _save_prompts(self):
        """Save prompts to file"""
        try:
            with open(self.prompts_file, 'w') as f:
                json.dump(self.prompts, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving prompts: {e}")
    
    def get_prompt(self, code_type: str) -> str:
        """Get current prompt for code type"""
        if code_type not in self.prompts:
            code_type = "other"
        
        return self.prompts[code_type]["prompt"]
    
    def update_prompt(self, code_type: str, new_prompt: str, feedback_summary: str):
        """Update prompt based on feedback"""
        if code_type not in self.prompts:
            code_type = "other"
        
        # Update the prompt
        old_version = self.prompts[code_type]["version"]
        new_version = f"{float(old_version) + 0.1:.1f}"
        
        self.prompts[code_type].update({
            "prompt": new_prompt,
            "version": new_version,
            "last_updated": datetime.now().isoformat(),
            "updates_count": self.prompts[code_type]["updates_count"] + 1,
        })
        
        # Add feedback summary to history
        self.prompts[code_type]["feedback_incorporated"].append({
            "timestamp": datetime.now().isoformat(),
            "feedback_summary": feedback_summary,
            "version": new_version
        })
        
        # Keep only last 10 feedback items
        if len(self.prompts[code_type]["feedback_incorporated"]) > 10:
            self.prompts[code_type]["feedback_incorporated"] = \
                self.prompts[code_type]["feedback_incorporated"][-10:]
        
        self._save_prompts()
        logger.info(f"Updated {code_type} prompt to version {new_version}")
    
    def get_prompt_info(self, code_type: str) -> Dict[str, Any]:
        """Get full prompt information including metadata"""
        if code_type not in self.prompts:
            code_type = "other"
        
        return self.prompts[code_type]
    
    def reset_prompts(self):
        """Reset all prompts to defaults"""
        self.prompts = self._load_prompts()
        if os.path.exists(self.prompts_file):
            os.remove(self.prompts_file)
        logger.info("Reset all prompts to defaults")

# Global instance
dynamic_prompt_manager = DynamicPromptManager()