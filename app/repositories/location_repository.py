from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.location import Location
from ..schemas.profile import LocationCreate, LocationUpdate

class LocationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_locations(self) -> List[Location]:
        return self.db.query(Location).filter(Location.is_deleted == False).all()

    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        return self.db.query(Location).filter(Location.id == location_id, Location.is_deleted == False).first()

    def create_location(self, data: LocationCreate) -> Location:
        location = Location(**data.dict())
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)
        return location

    def update_location(self, location_id: int, update_data: LocationUpdate) -> Optional[Location]:
        location = self.get_location_by_id(location_id)
        if location:
            for key, value in update_data.dict(exclude_unset=True).items():
                setattr(location, key, value)
            self.db.commit()
            self.db.refresh(location)
        return location

    def delete_location(self, location_id: int) -> bool:
        location = self.get_location_by_id(location_id)
        if location:
            location.is_deleted = True
            self.db.commit()
            return True
        return False 