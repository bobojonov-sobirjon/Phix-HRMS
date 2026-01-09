"""
Exception handlers for the application
"""
from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
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


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors, specifically handling empty string file uploads
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError instance
        
    Returns:
        JSONResponse with error format
    """
    if request.url.path.startswith("/api/"):
        errors = exc.errors()
        
        # Check if the error is about logo field expecting UploadFile but receiving string
        for error in errors:
            if (error.get("type") == "value_error" and 
                "logo" in error.get("loc", []) and 
                "Expected UploadFile" in error.get("msg", "")):
                # This is the empty string logo error - we can ignore it or return a better message
                logger.warning(
                    f"Empty string sent for logo field: {request.url.path}",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "error": str(error)
                    }
                )
                # Return a more user-friendly error message
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "error",
                        "msg": "Logo field should be a file upload or omitted entirely. Empty strings are not allowed."
                    }
                )
        
        # For other validation errors, return the standard format
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors()
            }
        )
        
        # Extract the first error message for user-friendly response
        first_error = errors[0] if errors else {}
        error_msg = first_error.get("msg", "Validation error")
        error_loc = " -> ".join(str(loc) for loc in first_error.get("loc", []))
        
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "msg": f"{error_loc}: {error_msg}" if error_loc else error_msg,
                "detail": errors
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
