from pydantic import BaseModel, Field
from typing import List, TypeVar, Generic
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(10, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Get limit for database query"""
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page"""
        return self.page < self.pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page"""
        return self.page > 1


def create_pagination_response(
    items: List[T],
    total: int,
    pagination: PaginationParams
) -> PaginatedResponse[T]:
    """
    Create a paginated response from items and pagination parameters
    
    Args:
        items: List of items for current page
        total: Total number of items
        pagination: Pagination parameters
        
    Returns:
        PaginatedResponse with calculated pagination info
    """
    pages = ceil(total / pagination.size) if total > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pages
    )
