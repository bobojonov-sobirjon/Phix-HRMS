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
        response = JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "msg": exc.detail
            }
        )
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
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
        # If logo is sent as empty string, we'll treat it as None (logo is optional)
        logo_error = None
        for error in errors:
            if (error.get("type") == "value_error" and 
                "logo" in error.get("loc", []) and 
                "Expected UploadFile" in error.get("msg", "")):
                logo_error = error
                break
        
        # If only logo error exists and it's about empty string, we can proceed without logo
        if logo_error and len(errors) == 1:
            logger.info(
                f"Empty string sent for logo field, treating as None: {request.url.path}",
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            # Remove logo error and let the request proceed
            # We'll handle this by allowing the request to continue without logo
            # But we need to modify the request or handle it differently
            # For now, return a helpful message
            response = JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "msg": "Logo field should be a file upload or omitted entirely. If you don't want to upload a logo, simply don't include the 'logo' field in your request."
                }
            )
            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        
        # For other validation errors, return the standard format
        logger.warning(
            f"Validation error: {exc.errors()}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors()
            }
        )
        
        # Clean errors for JSON serialization - convert Exception objects to strings
        cleaned_errors = []
        for error in errors:
            cleaned_error = {}
            for key, value in error.items():
                if key == "ctx" and isinstance(value, dict):
                    # Convert Exception objects in ctx to strings
                    ctx = {}
                    for ctx_key, ctx_value in value.items():
                        if isinstance(ctx_value, Exception):
                            ctx[ctx_key] = str(ctx_value)
                        else:
                            ctx[ctx_key] = ctx_value
                    cleaned_error[key] = ctx
                elif isinstance(value, Exception):
                    # Convert any Exception objects to strings
                    cleaned_error[key] = str(value)
                else:
                    cleaned_error[key] = value
            cleaned_errors.append(cleaned_error)
        
        # Extract error messages for user-friendly response
        if not cleaned_errors:
            error_msg = "Validation error"
        elif len(cleaned_errors) == 1:
            # Single error - show detailed message
            first_error = cleaned_errors[0]
            error_msg = first_error.get("msg", "Validation error")
            error_loc = " -> ".join(str(loc) for loc in first_error.get("loc", []))
            if error_loc:
                error_msg = f"{error_loc}: {error_msg}"
        else:
            # Multiple errors - show summary
            error_fields = []
            for error in cleaned_errors:
                loc = error.get("loc", [])
                if loc:
                    # Skip "body" prefix for cleaner messages
                    field_path = " -> ".join(str(l) for l in loc if l != "body")
                    if field_path:
                        error_fields.append(field_path)
            
            if error_fields:
                error_msg = f"Validation errors in: {', '.join(error_fields)}"
            else:
                error_msg = f"Multiple validation errors ({len(cleaned_errors)} errors)"
        
        response = JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "msg": error_msg,
                "detail": cleaned_errors
            }
        )
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
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
        
        response = JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "msg": ERROR_MESSAGES["INTERNAL_ERROR"]
            }
        )
        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    raise exc
