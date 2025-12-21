"""
Custom exception classes for the application
"""
from fastapi import HTTPException, status
from typing import Optional
from .constants import ERROR_MESSAGES


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class UnauthorizedException(BaseAPIException):
    """401 Unauthorized exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail or ERROR_MESSAGES["UNAUTHORIZED"]
        )


class ForbiddenException(BaseAPIException):
    """403 Forbidden exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail or ERROR_MESSAGES["FORBIDDEN"]
        )


class NotFoundException(BaseAPIException):
    """404 Not Found exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or ERROR_MESSAGES["NOT_FOUND"]
        )


class ValidationException(BaseAPIException):
    """400 Bad Request / Validation Error exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail or ERROR_MESSAGES["VALIDATION_ERROR"]
        )


class ConflictException(BaseAPIException):
    """409 Conflict exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail or ERROR_MESSAGES["CONFLICT"]
        )


class InternalServerException(BaseAPIException):
    """500 Internal Server Error exception"""
    
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail or ERROR_MESSAGES["INTERNAL_ERROR"]
        )
