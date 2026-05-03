#!/usr/bin/env python3
"""
Demo script to show the PR Review Automation System with Feedback Loop
This demonstrates how the system learns and improves from feedback
"""

import asyncio
import json
from datetime import datetime
from app.database import create_tables, get_db, PRReview, Feedback
from app.agents.main_agent import main_agent
from app.agents.dynamic_prompts import dynamic_prompt_manager
from sqlalchemy.orm import Session

class MockGroqClient:
    """Mock Groq client for demo purposes"""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """Mock LLM responses based on prompt content and call count"""
        self.call_count += 1
        
        # For feedback analysis
        if "feedback analyzer" in prompt.lower() or "analyze this feedback" in prompt.lower():
            return '''
{
    "feedback_type": "suggestion",
    "confidence": 0.9,
    "improvement_areas": ["security", "performance"],
    "specific_issues": ["Missing security analysis", "No performance considerations mentioned"],
    "suggested_changes": ["Add dedicated security review section", "Include performance impact analysis"],
    "prompt_updates": ["Add security vulnerability checklist", "Include performance considerations section"],
    "priority": "high"
}
'''
        
        # For prompt updates
        elif "prompt engineer" in prompt.lower() or "update the following" in prompt.lower():
            if "security" in prompt.lower():
                return '''
You are an expert backend code reviewer. Review this pull request focusing on:

1. **Architecture & Design:**
   - API design and RESTful principles
   - Database schema changes
   - Service layer organization
   - Separation of concerns

2. **Backend Best Practices:**
   - Error handling and logging
   - Input validation and sanitization
   - Database query optimization
   - Caching strategies

3. **Security (ENHANCED):**
   - Authentication and authorization
   - SQL injection prevention
   - Data encryption
   - Rate limiting
   - Input validation vulnerabilities
   - Security vulnerability checklist:
     * Check for hardcoded secrets
     * Validate all user inputs
     * Review authentication flows
     * Check authorization logic
     * Look for injection vulnerabilities

4. **Performance:**
   - Database indexing
   - Query efficiency
   - Memory usage
   - Scalability considerations
   - Performance impact analysis:
     * Assess computational complexity
     * Review memory usage patterns
     * Check for potential bottlenecks
     * Consider caching opportunities

5. **Testing:**
   - Unit test coverage
   - Integration test needs
   - API testing

PR Summary: {summary}
Code Analysis: {analysis}
Diff Content: {diff_content}

Please provide a structured code review with specific, actionable feedback, paying special attention to security vulnerabilities and performance implications.
'''
        
        # Regular review responses
        elif "summarizer" in prompt.lower():
            return """
**Code Summary:**
This PR adds JWT-based authentication to the API endpoints. The changes include:
- New authentication module with JWT token generation
- Token verification with expiration handling
- API route updates with authentication middleware
- Test coverage for authentication functionality
"""
        
        elif "analyzer" in prompt.lower():
            return """
**Diff Analysis:**
- Medium complexity changes introducing authentication logic
- Potential security risks with hardcoded secret key
- Good error handling but could be improved
- Missing input validation in some areas
"""
        
        elif "frontend" in prompt.lower():
            return "frontend"
        elif "backend" in prompt.lower():
            return "backend"
        else:
            # Generate different reviews based on call count to show improvement
            if self.call_count <= 3:
                return """
# 🤖 Automated Code Review

## Overview
This pull request introduces JWT-based authentication to the API.

## Issues Found
- Hardcoded secret key in auth.py
- Missing input validation

## Suggestions
- Use environment variables for secrets
- Add input validation

Overall: Good implementation but needs security improvements.
"""
            else:
                # Improved review after feedback
                return """
# 🤖 Automated Code Review (Enhanced)

## Overview
This pull request introduces JWT-based authentication to the API, which is a crucial security enhancement.

## 🔐 Security Analysis
**CRITICAL ISSUES:**
1. **Hardcoded Secret Key** (HIGH PRIORITY)
   - Location: `auth.py` line 9
   - Risk: Secret key is hardcoded as 'secret-key'
   - Fix: Use environment variable `JWT_SECRET_KEY`

2. **Input Validation Vulnerabilities**
   - Missing validation for `user_id` parameter
   - No type checking on inputs
   - Potential for injection attacks

**Security Checklist:**
- ❌ Hardcoded secrets found
- ❌ Input validation incomplete
- ✅ Authentication flow properly structured
- ❌ Authorization logic needs review

## ⚡ Performance Analysis
**Performance Impact:**
- Token generation: O(1) complexity ✅
- Memory usage: Minimal for JWT operations ✅
- Potential bottleneck: Database user lookups (not optimized)
- Caching opportunity: User data caching could improve performance

**Recommendations:**
- Implement user data caching
- Consider token refresh strategy
- Monitor JWT verification performance

## 🧪 Testing
- Good test coverage for main flows
- Missing edge case tests for malformed tokens
- Need integration tests for full auth flow

## Action Items
1. [ ] Fix hardcoded secret immediately
2. [ ] Add comprehensive input validation
3. [ ] Implement user data caching
4. [ ] Add security audit logging

**Security Score: 4/10** (due to critical issues)
**Performance Score: 7/10** (good design, room for optimization)
"""

async def demo_feedback_loop():
    """Demo the feedback loop functionality"""
    
    print("🔄 PR Review Automation System - Feedback Loop Demo")
    print("=" * 60)
    
    # Initialize database
    create_tables()
    print("✅ Database initialized")
    
    # Create mock groq client
    from app.agents import groq_client
    mock_client = MockGroqClient()
    
    # Replace the real client with mock for demo
    original_generate = groq_client.groq_client.generate_response
    groq_client.groq_client.generate_response = mock_client.generate_response
    
    # Mock PR data
    mock_pr_data = {
        'number': 456,
        'repository': 'demo-org/secure-api',
        'title': 'Add JWT authentication with security improvements',
        'description': 'Enhanced JWT implementation with better security practices',
        'diff': '''diff --git a/src/auth.py b/src/auth.py
+import jwt
+from datetime import datetime, timedelta
+
+def generate_token(user_id: int) -> str:
+    payload = {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(hours=24)}
+    return jwt.encode(payload, 'secret-key', algorithm='HS256')''',
        'files': ['src/auth.py', 'src/api/routes.py', 'tests/test_auth.py'],
        'author': 'security-dev',
        'base_branch': 'main',
        'head_branch': 'feature/jwt-auth-secure'
    }
    
    print(f"\n📋 Step 1: Initial PR Review")
    print("-" * 40)
    
    # Process initial PR
    result1 = await main_agent.process_pr(mock_pr_data)
    
    if result1.get('success'):
        print("✅ Initial review generated")
        print(f"\nCode Type: {result1.get('code_type')}")
        print(f"\nInitial Review:\n{result1.get('review')}")
        
        review_id = None
        try:
            db = next(get_db())
            review = db.query(PRReview).order_by(PRReview.id.desc()).first()
            review_id = review.id if review else None
        finally:
            db.close()
        
        if review_id:
            print(f"\n📋 Step 2: Receiving Feedback")
            print("-" * 40)
            
            # Simulate user feedback
            user_feedback = """
            @pr-bot feedback: The review missed important security considerations:
            1. The hardcoded secret key is a major security vulnerability
            2. There's no analysis of performance impact 
            3. Missing input validation security checks
            4. Should include a security vulnerability checklist
            5. Performance analysis section is missing
            
            Please improve future reviews to include dedicated security and performance sections.
            """
            
            print("👤 User Feedback Received:")
            print(user_feedback)
            
            print(f"\n📋 Step 3: Processing Feedback")
            print("-" * 40)
            
            # Process feedback
            feedback_result = await main_agent.process_feedback(review_id, user_feedback)
            
            if feedback_result.get('success'):
                print("✅ Feedback processed successfully")
                analysis = feedback_result.get('feedback_analysis', {})
                print(f"Feedback Type: {analysis.get('feedback_type')}")
                print(f"Priority: {analysis.get('priority')}")
                print(f"Improvement Areas: {', '.join(analysis.get('improvement_areas', []))}")
                print(f"Prompt Updated: {feedback_result.get('prompt_updated')}")
                
                if feedback_result.get('prompt_updated'):
                    print("\n🔄 Prompt has been updated based on feedback!")
                    
                    # Show prompt version info
                    prompt_info = dynamic_prompt_manager.get_prompt_info(result1.get('code_type'))
                    print(f"New Prompt Version: {prompt_info.get('version')}")
                    print(f"Updates Count: {prompt_info.get('updates_count')}")
                
                print(f"\n📋 Step 4: Testing Improved Review")
                print("-" * 40)
                
                # Process same PR again to show improvement
                mock_pr_data['number'] = 457  # Different PR number
                mock_pr_data['title'] = 'Add JWT authentication - Round 2'
                
                result2 = await main_agent.process_pr(mock_pr_data)
                
                if result2.get('success'):
                    print("✅ Improved review generated")
                    print(f"\nImproved Review:\n{result2.get('review')}")
                    
                    print(f"\n📊 Comparison:")
                    print("- Initial review: Basic security mention")
                    print("- Improved review: Detailed security checklist ✅")
                    print("- Initial review: No performance analysis")
                    print("- Improved review: Performance impact section ✅")
                    print("- System learned from feedback! 🎉")
                
    # Show statistics
    print(f"\n📊 System Statistics")
    print("-" * 40)
    
    try:
        db = next(get_db())
        total_reviews = db.query(PRReview).count()
        total_feedback = db.query(Feedback).count()
        
        print(f"Total Reviews: {total_reviews}")
        print(f"Total Feedback: {total_feedback}")
        
        # Show prompt evolution
        for code_type in ['frontend', 'backend', 'other']:
            info = dynamic_prompt_manager.get_prompt_info(code_type)
            print(f"{code_type.title()} Prompt Version: {info.get('version')} (Updated {info.get('updates_count')} times)")
            
    finally:
        db.close()
    
    # Restore original client
    groq_client.groq_client.generate_response = original_generate
    
    print(f"\n✨ Feedback Loop Demo Complete!")
    print("The system has successfully:")
    print("1. ✅ Generated initial review")
    print("2. ✅ Processed user feedback")
    print("3. ✅ Updated review approach")
    print("4. ✅ Improved subsequent reviews")
    print("5. ✅ Maintained learning history")

if __name__ == "__main__":
    print("🔄 This demo shows how the system learns from feedback!")
    print("Note: Uses mocked LLM responses to demonstrate the feedback loop.\n")
    asyncio.run(demo_feedback_loop())