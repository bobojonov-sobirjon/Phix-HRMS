from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import (
    CategoryCreate, 
    CategoryUpdate, 
    CategoryResponse, 
    CategoryWithChildren,
    CategorySearch
)
from app.utils.auth import get_current_user
from app.utils.decorators import handle_errors
from app.utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    validate_entity_exists
)
from app.models.user import User

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=CategoryResponse, summary="Create a new category")
@handle_errors
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new category or subcategory.
    
    - **name**: Category name (required)
    - **description**: Category description (optional)
    - **is_active**: Whether the category is active (default: True)
    - **parent_id**: Parent category ID for subcategories (optional)
    """
    repo = CategoryRepository(db)
    
    # Validate parent if provided
    if category.parent_id and not repo.is_valid_parent(category.parent_id):
        raise bad_request_error("Invalid parent category")
    
    return repo.create(category)


@router.get("/", response_model=List[CategoryResponse], summary="Get all categories with filters")
async def get_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    name: Optional[str] = Query(None, description="Search by category name"),
    is_main: Optional[bool] = Query(None, description="Filter main categories (true) or subcategories (false)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: Session = Depends(get_db)
):
    """
    Get all categories with optional filters:
    
    - **name**: Search by category name (case-insensitive)
    - **is_main**: Filter main categories (true) or subcategories (false)
    - **is_active**: Filter by active status (true/false)
    - **skip/limit**: Pagination parameters
    """
    repo = CategoryRepository(db)
    
    # If name search is provided, use search by name
    if name:
        return repo.search_by_name(name, skip=skip, limit=limit)
    
    # If is_main filter is provided, filter by main/sub categories
    if is_main is not None:
        if is_main:
            # Get main categories only
            if is_active is not None:
                return repo.get_categories_only_with_filter(is_active, skip=skip, limit=limit)
            return repo.get_categories_only(skip=skip, limit=limit)
        else:
            # Get subcategories only
            if is_active is not None:
                return repo.get_all_subcategories_with_filter(is_active, skip=skip, limit=limit)
            return repo.get_all_subcategories(skip=skip, limit=limit)
    
    # If only is_active filter is provided
    if is_active is not None:
        return repo.get_all_with_filter(is_active, skip=skip, limit=limit)
    
    # No filters - return all categories
    return repo.get_all(skip=skip, limit=limit)


@router.get("/main", response_model=List[CategoryResponse], summary="Get main categories only")
async def get_main_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: Session = Depends(get_db)
):
    """
    Get only main categories (categories without parent) with optional active status filter.
    
    - **is_active**: Filter by active status (true for active, false for inactive, null for all)
    """
    repo = CategoryRepository(db)
    if is_active is not None:
        return repo.get_categories_only_with_filter(is_active, skip=skip, limit=limit)
    return repo.get_categories_only(skip=skip, limit=limit)


@router.get("/subcategories/{parent_id}", response_model=List[CategoryResponse], summary="Get subcategories by parent ID")
async def get_subcategories_by_parent(
    parent_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status (true/false)"),
    db: Session = Depends(get_db)
):
    """
    Get subcategories for a specific parent category with optional active status filter.
    
    - **parent_id**: ID of the parent category
    - **is_active**: Filter by active status (true for active, false for inactive, null for all)
    """
    repo = CategoryRepository(db)
    if is_active is not None:
        return repo.get_subcategories_with_filter(parent_id, is_active, skip=skip, limit=limit)
    return repo.get_subcategories(parent_id, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse, summary="Get category by ID")
@handle_errors
async def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID.
    """
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    validate_entity_exists(category, "Category")
    return category


@router.put("/{category_id}", response_model=CategoryResponse, summary="Update category")
@handle_errors
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing category.
    """
    repo = CategoryRepository(db)
    
    # Validate parent if provided
    if category_update.parent_id and not repo.is_valid_parent(category_update.parent_id):
        raise bad_request_error("Invalid parent category")
    
    category = repo.update(category_id, category_update)
    validate_entity_exists(category, "Category")
    return category


@router.delete("/{category_id}", summary="Delete category")
@handle_errors
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a category. If the category has children, it will be soft deleted (marked as inactive).
    """
    repo = CategoryRepository(db)
    success = repo.delete(category_id)
    if not success:
        raise not_found_error("Category not found")
    
    return {"message": "Category deleted successfully"}
