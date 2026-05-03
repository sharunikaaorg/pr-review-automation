"""
Health check utilities for monitoring system components.
"""

import time
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


def check_groq_connection() -> Dict[str, Any]:
    """Verify Groq API connectivity."""
    if not settings.GROQ_API_KEY:
        return {"status": "unconfigured", "latency_ms": None}
    try:
        from groq import Groq
        start = time.time()
        client = Groq(api_key=settings.GROQ_API_KEY)
        client.models.list()
        latency = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        logger.error(f"Groq health check failed: {e}")
        return {"status": "error", "error": str(e), "latency_ms": None}


def check_github_connection() -> Dict[str, Any]:
    """Verify GitHub API connectivity."""
    if not settings.GITHUB_TOKEN:
        return {"status": "unconfigured", "latency_ms": None}
    try:
        import requests
        start = time.time()
        r = requests.get(
            "https://api.github.com/rate_limit",
            headers={"Authorization": f"token {settings.GITHUB_TOKEN}"},
            timeout=5,
        )
        latency = round((time.time() - start) * 1000)
        if r.status_code == 200:
            remaining = r.json().get("rate", {}).get("remaining", "unknown")
            return {"status": "ok", "latency_ms": latency, "rate_remaining": remaining}
        return {"status": "error", "http_status": r.status_code, "latency_ms": latency}
    except Exception as e:
        logger.error(f"GitHub health check failed: {e}")
        return {"status": "error", "error": str(e), "latency_ms": None}


def check_database() -> Dict[str, Any]:
    """Verify database connectivity."""
    try:
        from app.database import get_db
        start = time.time()
        db = next(get_db())
        db.execute("SELECT 1")
        latency = round((time.time() - start) * 1000)
        db.close()
        return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "error", "error": str(e), "latency_ms": None}


def get_full_health() -> Dict[str, Any]:
    """Run all health checks and return combined status."""
    checks = {
        "groq": check_groq_connection(),
        "github": check_github_connection(),
        "database": check_database(),
    }
    all_ok = all(c["status"] == "ok" for c in checks.values())
    return {"healthy": all_ok, "checks": checks}
