from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.location_repository import LocationRepository
from ..schemas.profile import LocationResponse, LocationCreate, LocationUpdate
from typing import List
from ..models.user import User
from ..utils.auth import get_current_user
import os

router = APIRouter(prefix="/locations", tags=["Locations"])

@router.get("/", response_model=List[LocationResponse], tags=["Locations"])
def get_locations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request = None):
    repo = LocationRepository(db)
    locations = repo.get_all_locations()
    base_url = str(request.base_url).rstrip("/") if request else ""
    result = []
    for loc in locations:
        loc_data = LocationResponse.from_orm(loc).dict()
        if loc_data["flag_image"] and not loc_data["flag_image"].startswith("http"):
            loc_data["flag_image"] = f"{base_url}{loc_data['flag_image']}"
        result.append(loc_data)
    return result

@router.get("/{location_id}", response_model=LocationResponse, tags=["Locations"])
def get_location(location_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LocationRepository(db)
    location = repo.get_location_by_id(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.post("/", response_model=LocationResponse, tags=["Locations"])
async def create_location(
    name: str = Form(...),
    code: str = Form(...),
    flag_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    # Save flag_image if provided
    flag_image_path = None
    if flag_image and flag_image.content_type.startswith('image/'):
        upload_dir = "static/flags"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{name}_{flag_image.filename}"
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await flag_image.read())
        flag_image_path = f"/{file_path.replace('\\', '/')}"

    # Create location
    repo = LocationRepository(db)
    location = repo.create_location(LocationCreate(
        name=name,
        code=code,
        flag_image=flag_image_path
    ))

    # Add base URL to flag_image in response
    location_data = LocationResponse.from_orm(location).dict()
    if location_data["flag_image"]:
        base_url = str(request.base_url).rstrip("/")
        location_data["flag_image"] = f"{base_url}{location_data['flag_image']}"
    return location_data

@router.patch("/{location_id}", response_model=LocationResponse, tags=["Locations"])
def update_location(location_id: int, data: LocationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LocationRepository(db)
    updated = repo.update_location(location_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Location not found")
    return updated

@router.delete("/{location_id}", tags=["Locations"])
def delete_location(location_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LocationRepository(db)
    if not repo.delete_location(location_id):
        raise HTTPException(status_code=404, detail="Location not found")
    return {"message": "Location deleted successfully"} 