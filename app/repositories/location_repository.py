from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.location import Location
from ..schemas.profile import LocationCreate, LocationUpdate
from .base_repository import BaseRepository


class LocationRepository(BaseRepository[Location]):
    """Repository for Location model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Location)
    
    def get_all_locations(self) -> List[Location]:
        """Get all locations (excluding deleted)"""
        return self.get_all(include_deleted=False)
    
    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Get location by ID (excluding deleted)"""
        return self.get_by_id(location_id, include_deleted=False)
    
    def create_location(self, data: LocationCreate) -> Location:
        """Create a new location"""
        return self.create(data.dict())
    
    def update_location(self, location_id: int, update_data: LocationUpdate) -> Optional[Location]:
        """Update location"""
        return self.update(location_id, update_data, exclude_unset=True)
    
    def delete_location(self, location_id: int) -> bool:
        """Soft delete location"""
        return self.delete(location_id, hard_delete=False) 