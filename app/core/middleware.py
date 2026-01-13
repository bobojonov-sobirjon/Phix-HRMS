"""
Custom middleware for the application
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response, RedirectResponse
from typing import Callable
from .logging_config import logger
import time

MAX_UPLOAD_SIZE = 100 * 1024 * 1024


class CORSHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure CORS headers are always present in responses"""
    
    async def dispatch(self, request: StarletteRequest, call_next: Callable) -> Response:
        """Add CORS headers to all responses"""
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            # Add CORS headers to OPTIONS response
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Expose-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "false"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # For other requests, process normally and add CORS headers
        response = await call_next(request)
        
        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "false"
        response.headers["Access-Control-Max-Age"] = "3600"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and increasing body size limit"""
    
    async def dispatch(self, request: StarletteRequest, call_next: Callable) -> Response:
        """Log incoming requests and increase body size limit"""
        start_time = time.time()
        
        if request.url.path.startswith("/api/v1/chat/ws"):
            logger.info(
                f"WebSocket connection attempt: {request.method} {request.url.path}",
                extra={
                    "query_params": request.url.query,
                    "client_ip": request.client.host if request.client else None
                }
            )
        
        if hasattr(request, '_form'):
            request._form = None
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )
        
        return response


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging errors"""
    
    async def dispatch(self, request: StarletteRequest, call_next: Callable) -> Response:
        """Log errors"""
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                }
            )
            raise
