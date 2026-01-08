from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..repositories.education_facility_repository import EducationFacilityRepository
from ..schemas.education_facility import (
    EducationFacilityCreate,
    EducationFacilityUpdate,
    EducationFacilityResponse,
    EducationFacilityListResponse
)
from ..utils.auth import get_current_user
from ..utils.decorators import handle_errors
from ..utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    validate_entity_exists
)
from ..models.user import User
from ..models.education_facility import EducationFacility

router = APIRouter(tags=["Education Facilities"])

@router.post("/education-facilities", response_model=EducationFacilityResponse)
@handle_errors
async def create_education_facility(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str = Query(..., description="Education facility name", example="Mansoura University"),
    icon: str = Query(None, description="Icon URL or path", example="https://example.com/icon.png"),
    country: str = Query(None, description="Country name", example="Egypt")
):
    """Create a new education facility"""
    repository = EducationFacilityRepository(db)
    
    existing_facility = repository.get_education_facility_by_name(name)
    if existing_facility:
        raise bad_request_error("Education facility with this name already exists")
    
    facility_data = {"name": name}
    if icon:
        facility_data["icon"] = icon
    if country:
        facility_data["country"] = country
    
    facility = repository.create_education_facility(facility_data)
    return facility

@router.get("/education-facilities/{facility_id}", response_model=EducationFacilityResponse)
@handle_errors
async def get_education_facility(
    facility_id: int,
    db: Session = Depends(get_db)
):
    """Get education facility by ID"""
    repository = EducationFacilityRepository(db)
    facility = repository.get_education_facility_by_id(facility_id)
    validate_entity_exists(facility, "Education facility")
    return facility

@router.get("/education-facilities", response_model=EducationFacilityListResponse)
async def get_education_facilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None, description="Search by facility name"),
    country: str = Query(None, description="Filter by country"),
    db: Session = Depends(get_db)
):
    """Get all education facilities with optional search and filtering"""
    repository = EducationFacilityRepository(db)
    
    if search:
        facilities = repository.search_education_facilities(search, skip, limit)
        total = len(facilities)
    elif country:
        facilities = repository.get_education_facilities_by_country(country, skip, limit)
        total = len(facilities)
    else:
        facilities = repository.get_all_education_facilities(skip, limit)
        total = db.query(repository.db.query(EducationFacility).filter(
            EducationFacility.is_deleted == False
        ).subquery()).count()
    
    return EducationFacilityListResponse(
        facilities=facilities,
        total=total,
        skip=skip,
        limit=limit
    )

@router.put("/education-facilities/{facility_id}", response_model=EducationFacilityResponse)
@handle_errors
async def update_education_facility(
    facility_id: int,
    facility_data: EducationFacilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update education facility"""
    repository = EducationFacilityRepository(db)
    
    existing_facility = repository.get_education_facility_by_id(facility_id)
    validate_entity_exists(existing_facility, "Education facility")
    
    if facility_data.name and facility_data.name != existing_facility.name:
        duplicate_facility = repository.get_education_facility_by_name(facility_data.name)
        if duplicate_facility:
            raise bad_request_error("Education facility with this name already exists")
    
    update_data = {k: v for k, v in facility_data.dict().items() if v is not None}
    
    if update_data:
        facility = repository.update_education_facility(facility_id, update_data)
        return facility
    
    return existing_facility

@router.delete("/education-facilities/{facility_id}")
@handle_errors
async def delete_education_facility(
    facility_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete education facility (soft delete)"""
    repository = EducationFacilityRepository(db)
    
    existing_facility = repository.get_education_facility_by_id(facility_id)
    validate_entity_exists(existing_facility, "Education facility")
    
    success = repository.delete_education_facility(facility_id)
    
    if not success:
        raise bad_request_error("Failed to delete education facility")
    
    return {"message": "Education facility deleted successfully"}

@router.get("/education-facilities/search/autocomplete")
async def search_education_facilities_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Search education facilities for autocomplete (returns only names)"""
    repository = EducationFacilityRepository(db)
    facilities = repository.search_education_facilities(q, 0, limit)
    
    return {
        "suggestions": [facility.name for facility in facilities],
        "total": len(facilities)
    }
