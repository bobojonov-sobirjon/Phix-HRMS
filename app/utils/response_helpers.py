"""
Helper functions for API responses
"""
from fastapi import HTTPException, status
from typing import Any, Optional
from ..schemas.common import SuccessResponse, MessageResponse, ErrorResponse


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> SuccessResponse:
    """
    Create a success response
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        SuccessResponse object
    """
    return SuccessResponse(msg=message, data=data)


def message_response(
    message: str,
    status_code: int = status.HTTP_200_OK
) -> MessageResponse:
    """
    Create a message response
    
    Args:
        message: Response message
        status_code: HTTP status code
        
    Returns:
        MessageResponse object
    """
    return MessageResponse(message=message)


def not_found_error(message: str = "Resource not found") -> HTTPException:
    """
    Create a 404 Not Found error
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 404 status
    """
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=message
    )


def bad_request_error(message: str = "Bad request") -> HTTPException:
    """
    Create a 400 Bad Request error
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 400 status
    """
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )


def unauthorized_error(message: str = "Unauthorized") -> HTTPException:
    """
    Create a 401 Unauthorized error
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 401 status
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message
    )


def forbidden_error(message: str = "Forbidden") -> HTTPException:
    """
    Create a 403 Forbidden error
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 403 status
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )


def internal_server_error(message: str = "Internal server error") -> HTTPException:
    """
    Create a 500 Internal Server Error
    
    Args:
        message: Error message
        
    Returns:
        HTTPException with 500 status
    """
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )


def validate_entity_exists(entity: Optional[Any], entity_name: str = "Entity") -> None:
    """
    Validate that entity exists, raise 404 if not
    
    Args:
        entity: Entity to validate
        entity_name: Name of entity for error message
        
    Raises:
        HTTPException: 404 if entity is None
    """
    if entity is None:
        raise not_found_error(f"{entity_name} not found")


def validate_ownership(entity_user_id: int, current_user_id: int, entity_name: str = "Entity") -> None:
    """
    Validate that current user owns the entity
    
    Args:
        entity_user_id: User ID of entity owner
        current_user_id: Current user ID
        entity_name: Name of entity for error message
        
    Raises:
        HTTPException: 403 if user doesn't own entity
    """
    if entity_user_id != current_user_id:
        raise forbidden_error(f"You don't have permission to access this {entity_name.lower()}")
