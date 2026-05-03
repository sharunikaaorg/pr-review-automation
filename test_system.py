#!/usr/bin/env python3
"""
Simple test script for the PR Review Automation System
"""

import asyncio
import json
from app.agents.main_agent import main_agent
from app.database import create_tables

async def test_system():
    """Test the system with mock PR data"""
    
    print("🚀 Testing PR Review Automation System...")
    
    # Initialize database
    create_tables()
    print("✅ Database initialized")
    
    # Mock PR data for testing
    mock_pr_data = {
        'number': 123,
        'repository': 'test-org/test-repo',
        'title': 'Add user authentication feature',
        'description': 'This PR adds JWT-based authentication to the API endpoints',
        'diff': '''
diff --git a/src/auth.py b/src/auth.py
new file mode 100644
index 0000000..123456
--- /dev/null
+++ b/src/auth.py
@@ -0,0 +1,20 @@
+import jwt
+from datetime import datetime, timedelta
+
+def generate_token(user_id: int) -> str:
+    """Generate JWT token for user"""
+    payload = {
+        'user_id': user_id,
+        'exp': datetime.utcnow() + timedelta(hours=24)
+    }
+    return jwt.encode(payload, 'secret-key', algorithm='HS256')
+
+def verify_token(token: str) -> dict:
+    """Verify JWT token"""
+    try:
+        payload = jwt.decode(token, 'secret-key', algorithms=['HS256'])
+        return payload
+    except jwt.ExpiredSignatureError:
+        raise Exception("Token has expired")
+    except jwt.InvalidTokenError:
+        raise Exception("Invalid token")
''',
        'files': ['src/auth.py', 'src/api/routes.py', 'tests/test_auth.py'],
        'author': 'developer123',
        'base_branch': 'main',
        'head_branch': 'feature/auth',
        'url': 'https://github.com/test-org/test-repo/pull/123'
    }
    
    print("📊 Processing mock PR data...")
    
    try:
        # Process through main agent
        result = await main_agent.process_pr(mock_pr_data)
        
        if result.get('success'):
            print("✅ PR processed successfully!")
            print(f"\n📋 Code Type: {result.get('code_type')}")
            print(f"\n📝 Summary:\n{result.get('summary')}")
            print(f"\n🔍 Analysis:\n{result.get('analysis')}")
            print(f"\n📖 Review:\n{result.get('review')}")
        else:
            print(f"❌ PR processing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_system())