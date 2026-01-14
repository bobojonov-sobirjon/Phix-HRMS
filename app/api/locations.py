from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositories.location_repository import LocationRepository
from ..schemas.profile import LocationResponse, LocationCreate, LocationUpdate
from ..schemas.common import SuccessResponse
from ..utils.decorators import handle_errors
from ..utils.response_helpers import success_response, not_found_error, validate_entity_exists, bad_request_error, forbidden_error
from ..utils.permissions import is_admin_user
from typing import List, Optional
from ..models.user import User
from ..utils.auth import get_current_user, get_current_user_optional
import os

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/", response_model=SuccessResponse, tags=["Locations"])
@handle_errors
async def get_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Get all locations"""
    repo = LocationRepository(db)
    locations = repo.get_all_locations()
    base_url = str(request.base_url).rstrip("/") if request else ""
    result = []
    for loc in locations:
        loc_data = LocationResponse.model_validate(loc).dict()
        if loc_data["flag_image"] and not loc_data["flag_image"].startswith("http"):
            loc_data["flag_image"] = f"{base_url}{loc_data['flag_image']}"
        result.append(loc_data)
    return success_response(
        data=result,
        message="Locations retrieved successfully"
    )

@router.get("/{location_id}", response_model=SuccessResponse, tags=["Locations"])
@handle_errors
async def get_location(
    location_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get location by ID"""
    repo = LocationRepository(db)
    location = repo.get_location_by_id(location_id)
    validate_entity_exists(location, "Location")
    return success_response(
        data=LocationResponse.model_validate(location),
        message="Location retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse, tags=["Locations"])
@handle_errors
async def create_location(
    location_data: LocationCreate = None,
    name: str = Form(None),
    code: str = Form(None),
    phone_code: str = Form(None),
    flag_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Create a new location"""
    if location_data:
        name = location_data.name
        code = location_data.code
        phone_code = location_data.phone_code
        flag_image_path = location_data.flag_image
    else:
        if not name or not code:
            raise bad_request_error("name and code are required")
        flag_image_path = None
        if flag_image and flag_image.content_type.startswith('image/'):
            upload_dir = "static/flags"
            os.makedirs(upload_dir, exist_ok=True)
            filename = f"{name}_{flag_image.filename}"
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as buffer:
                content = await flag_image.read()
                buffer.write(content)
            normalized_path = file_path.replace('\\', '/')
            flag_image_path = f"/{normalized_path}"

    repo = LocationRepository(db)
    location = repo.create_location(LocationCreate(
        name=name,
        code=code,
        phone_code=phone_code,
        flag_image=flag_image_path
    ))

    location_data = LocationResponse.model_validate(location).dict()
    if location_data["flag_image"]:
        base_url = str(request.base_url).rstrip("/")
        location_data["flag_image"] = f"{base_url}{location_data['flag_image']}"
    
    return success_response(
        data=location_data,
        message="Location created successfully"
    )

@router.patch("/{location_id}", response_model=SuccessResponse, tags=["Locations"])
@handle_errors
async def update_location(
    location_id: int,
    data: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update location (admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can update locations")
    repo = LocationRepository(db)
    updated = repo.update_location(location_id, data)
    validate_entity_exists(updated, "Location")
    return success_response(
        data=updated,
        message="Location updated successfully"
    )

@router.delete("/{location_id}", response_model=SuccessResponse, tags=["Locations"])
@handle_errors
async def delete_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete location (admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can delete locations")
    repo = LocationRepository(db)
    if not repo.delete_location(location_id):
        raise not_found_error("Location not found")
    return success_response(
        data=None,
        message="Location deleted successfully"
    ) 