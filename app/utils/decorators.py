"""
Common decorators for API endpoints
"""
from functools import wraps
from fastapi import HTTPException, status
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in API endpoints
    
    Usage:
        @router.get("/")
        @handle_errors
        async def get_items(...):
            ...
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error: {str(e)}"
            )
    
    # Return appropriate wrapper based on whether function is async
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def validate_not_found(func: Callable) -> Callable:
    """
    Decorator to validate entity exists before operation
    
    Usage:
        @router.get("/{id}")
        @validate_not_found
        async def get_item(id: int, repo: Repository = Depends(...)):
            item = repo.get_by_id(id)
            if not item:
                raise HTTPException(404, "Not found")
            return item
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    import inspect
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper
