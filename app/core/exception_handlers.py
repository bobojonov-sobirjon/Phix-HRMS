"""
Exception handlers for the application
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .logging_config import logger
from .constants import ERROR_MESSAGES
import traceback


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with standardized error format
    
    Args:
        request: FastAPI request object
        exc: HTTPException instance
        
    Returns:
        JSONResponse with error format
    """
    if request.url.path.startswith("/api/"):
        logger.warning(
            f"HTTP {exc.status_code} error: {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "msg": exc.detail
            }
        )
    raise exc


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions with standardized error format
    
    Args:
        request: FastAPI request object
        exc: Exception instance
        
    Returns:
        JSONResponse with error format
    """
    if request.url.path.startswith("/api/"):
        logger.error(
            f"Unhandled exception: {type(exc).__name__}",
            exc_info=True,
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "msg": ERROR_MESSAGES["INTERNAL_ERROR"]
            }
        )
    raise exc
