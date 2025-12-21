"""
Pagination utilities and validation
"""
from typing import Optional
from pydantic import BaseModel, validator
from .constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, MIN_PAGE_SIZE, DEFAULT_PAGE


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""
    
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be greater than 0')
        return v
    
    @validator('page_size')
    def validate_page_size(cls, v):
        if v < MIN_PAGE_SIZE:
            raise ValueError(f'Page size must be at least {MIN_PAGE_SIZE}')
        if v > MAX_PAGE_SIZE:
            raise ValueError(f'Page size cannot exceed {MAX_PAGE_SIZE}')
        return v
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and page_size"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit (same as page_size)"""
        return self.page_size


def validate_pagination_params(
    page: Optional[int] = None,
    page_size: Optional[int] = None
) -> PaginationParams:
    """
    Validate and create pagination parameters
    
    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: DEFAULT_PAGE_SIZE)
        
    Returns:
        PaginationParams instance
    """
    return PaginationParams(
        page=page or DEFAULT_PAGE,
        page_size=page_size or DEFAULT_PAGE_SIZE
    )
