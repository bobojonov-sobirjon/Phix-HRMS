"""
Custom middleware for the application
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from typing import Callable
from .logging_config import logger
import time

MAX_UPLOAD_SIZE = 100 * 1024 * 1024


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
