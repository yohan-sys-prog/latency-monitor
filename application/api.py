"""
Production-grade API blueprint for versioned routes with proper error handling.
Implements V1 API with validation, CORS, and standard response formats.
"""

from flask import Blueprint, jsonify, request
from functools import wraps

# API response wrapper
def api_response(data=None, error=None, status=200):
    """Standard API response format."""
    if error:
        return jsonify({
            "status": "error",
            "error": error,
        }), status
    return jsonify({
        "status": "success",
        "data": data,
    }), status


def validate_json(*required_fields):
    """Decorator to validate required JSON fields."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json() or {}
            missing = [field for field in required_fields if field not in data]
            if missing:
                return api_response(error=f"Missing required fields: {', '.join(missing)}", status=400)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_v1_api():
    """Create the V1 API blueprint with routes."""
    api = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    
    # Routes will be added by the dashboard module
    return api


class APIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code


class RateLimiter:
    """Simple rate limiter for API endpoints."""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key, max_requests=100, window_seconds=60):
        """Check if request is allowed (simple in-memory limiter)."""
        import time
        now = time.time()
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
        
        if len(self.requests[key]) >= max_requests:
            return False
        
        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


def rate_limit(max_requests=100, window_seconds=60):
    """Decorator to apply rate limiting."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Use client IP or authenticated user as key
            if hasattr(request, 'user'):
                key = request.user.get('username', request.remote_addr)
            else:
                key = request.remote_addr
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                return api_response(error="Rate limit exceeded", status=429)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
