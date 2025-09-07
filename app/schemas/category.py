from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(True, description="Whether the category is active")


class CategoryCreate(CategoryBase):
    parent_id: Optional[int] = Field(None, description="Parent category ID for subcategories")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether the category is active")
    parent_id: Optional[int] = Field(None, description="Parent category ID for subcategories")


class CategoryResponse(CategoryBase):
    id: int
    parent_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CategoryWithChildren(CategoryResponse):
    children: List['CategoryResponse'] = []
    parent: Optional['CategoryResponse'] = None


class CategorySearch(BaseModel):
    name: Optional[str] = Field(None, description="Search by category name")
    parent_id: Optional[int] = Field(None, description="Search by parent category ID")
    is_active: Optional[bool] = Field(None, description="Filter by active status")


# Update forward references
CategoryWithChildren.model_rebuild()
