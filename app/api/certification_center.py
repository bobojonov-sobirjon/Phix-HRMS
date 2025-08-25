from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..repositories.certification_center_repository import CertificationCenterRepository
from ..schemas.certification_center import (
    CertificationCenterCreate,
    CertificationCenterUpdate,
    CertificationCenterResponse,
    CertificationCenterListResponse
)
from ..utils.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/certification-centers", tags=["Certification centers"])

@router.post("/", response_model=CertificationCenterResponse)
def create_certification_center(
    data: CertificationCenterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new certification center"""
    repo = CertificationCenterRepository(db)
    
    # Check if certification center with same name already exists
    existing_center = repo.get_certification_center_by_name(data.name)
    if existing_center:
        raise HTTPException(status_code=400, detail="Certification center with this name already exists")
    
    return repo.create_certification_center(data.dict())

@router.get("/", response_model=List[CertificationCenterListResponse])
def get_certification_centers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Search by name"),
    db: Session = Depends(get_db)
):
    """Get all certification centers with optional search and pagination"""
    repo = CertificationCenterRepository(db)
    
    if search:
        return repo.search_certification_centers(search, skip, limit)
    else:
        return repo.get_all_certification_centers(skip, limit)

@router.get("/{center_id}", response_model=CertificationCenterResponse)
def get_certification_center(
    center_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific certification center by ID"""
    repo = CertificationCenterRepository(db)
    center = repo.get_certification_center_by_id(center_id)
    
    if not center:
        raise HTTPException(status_code=404, detail="Certification center not found")
    
    return center

@router.put("/{center_id}", response_model=CertificationCenterResponse)
def update_certification_center(
    center_id: int,
    data: CertificationCenterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a certification center"""
    repo = CertificationCenterRepository(db)
    
    # Check if center exists
    existing_center = repo.get_certification_center_by_id(center_id)
    if not existing_center:
        raise HTTPException(status_code=404, detail="Certification center not found")
    
    # Check if new name conflicts with existing centers
    if data.name and data.name != existing_center.name:
        name_conflict = repo.get_certification_center_by_name(data.name)
        if name_conflict:
            raise HTTPException(status_code=400, detail="Certification center with this name already exists")
    
    # Filter out None values
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    
    if not update_data:
        return existing_center
    
    updated_center = repo.update_certification_center(center_id, update_data)
    if not updated_center:
        raise HTTPException(status_code=500, detail="Failed to update certification center")
    
    return updated_center

@router.delete("/{center_id}")
def delete_certification_center(
    center_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a certification center (soft delete)"""
    repo = CertificationCenterRepository(db)
    
    # Check if center exists
    existing_center = repo.get_certification_center_by_id(center_id)
    if not existing_center:
        raise HTTPException(status_code=404, detail="Certification center not found")
    
    success = repo.delete_certification_center(center_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete certification center")
    
    return {"message": "Certification center deleted successfully"}
