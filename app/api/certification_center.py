from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..repositories.certification_center_repository import CertificationCenterRepository
from ..schemas.certification_center import (
    CertificationCenterCreate,
    CertificationCenterUpdate,
    CertificationCenterResponse,
    CertificationCenterListResponse
)
from ..utils.auth import get_current_user
from ..utils.decorators import handle_errors
from ..utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    validate_entity_exists,
    forbidden_error
)
from ..utils.permissions import is_admin_user
from ..models.user import User

router = APIRouter(prefix="/certification-centers", tags=["Certification centers"])

@router.post("/", response_model=CertificationCenterResponse)
@handle_errors
async def create_certification_center(
    data: CertificationCenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new certification center"""
    repo = CertificationCenterRepository(db)
    
    existing_center = repo.get_certification_center_by_name(data.name)
    if existing_center:
        raise bad_request_error("Certification center with this name already exists")
    
    try:
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        data_dict = data.model_dump() if hasattr(data, 'model_dump') else data.dict()
        certification_center = repo.create_certification_center(data_dict)
        # Use model_validate for Pydantic v2, from_orm for v1
        if hasattr(CertificationCenterResponse, 'model_validate'):
            return CertificationCenterResponse.model_validate(certification_center)
        else:
            return CertificationCenterResponse.from_orm(certification_center)
    except Exception as e:
        error_msg = str(e).lower()
        if 'unique' in error_msg or 'duplicate' in error_msg or 'already exists' in error_msg:
            raise bad_request_error("Certification center with this name already exists")
        import traceback
        traceback.print_exc()
        raise bad_request_error(f"Failed to create certification center: {str(e)}")

@router.get("/", response_model=List[CertificationCenterListResponse])
@handle_errors
async def get_certification_centers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """Get all certification centers with optional search and pagination"""
    repo = CertificationCenterRepository(db)
    
    if search:
        centers = repo.search_certification_centers(search, skip, limit)
    else:
        centers = repo.get_all_certification_centers(skip, limit)
    
    # Use model_validate for Pydantic v2, from_orm for v1
    if hasattr(CertificationCenterListResponse, 'model_validate'):
        return [CertificationCenterListResponse.model_validate(center) for center in centers]
    else:
        return [CertificationCenterListResponse.from_orm(center) for center in centers]

@router.get("/{center_id}", response_model=CertificationCenterResponse)
@handle_errors
async def get_certification_center(
    center_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific certification center by ID"""
    repo = CertificationCenterRepository(db)
    center = repo.get_certification_center_by_id(center_id)
    validate_entity_exists(center, "Certification center")
    # Use model_validate for Pydantic v2, from_orm for v1
    if hasattr(CertificationCenterResponse, 'model_validate'):
        return CertificationCenterResponse.model_validate(center)
    else:
        return CertificationCenterResponse.from_orm(center)

@router.put("/{center_id}", response_model=CertificationCenterResponse)
@handle_errors
async def update_certification_center(
    center_id: int,
    data: CertificationCenterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a certification center (admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can update certification centers")
    repo = CertificationCenterRepository(db)
    
    existing_center = repo.get_certification_center_by_id(center_id)
    validate_entity_exists(existing_center, "Certification center")
    
    if data.name and data.name != existing_center.name:
        name_conflict = repo.get_certification_center_by_name(data.name)
        if name_conflict:
            raise bad_request_error("Certification center with this name already exists")
    
    # Use model_dump() for Pydantic v2, fallback to dict() for v1
    data_dict = data.model_dump(exclude_unset=True) if hasattr(data, 'model_dump') else data.dict(exclude_unset=True)
    update_data = {k: v for k, v in data_dict.items() if v is not None}
    
    if not update_data:
        # Use model_validate for Pydantic v2, from_orm for v1
        if hasattr(CertificationCenterResponse, 'model_validate'):
            return CertificationCenterResponse.model_validate(existing_center)
        else:
            return CertificationCenterResponse.from_orm(existing_center)
    
    updated_center = repo.update_certification_center(center_id, update_data)
    if not updated_center:
        raise bad_request_error("Failed to update certification center")
    
    # Use model_validate for Pydantic v2, from_orm for v1
    if hasattr(CertificationCenterResponse, 'model_validate'):
        return CertificationCenterResponse.model_validate(updated_center)
    else:
        return CertificationCenterResponse.from_orm(updated_center)

@router.delete("/{center_id}")
@handle_errors
async def delete_certification_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a certification center (soft delete, admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can delete certification centers")
    repo = CertificationCenterRepository(db)
    
    existing_center = repo.get_certification_center_by_id(center_id)
    validate_entity_exists(existing_center, "Certification center")
    
    success = repo.delete_certification_center(center_id)
    if not success:
        raise bad_request_error("Failed to delete certification center")
    
    return {"message": "Certification center deleted successfully"}
