from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.education_facility import EducationFacility

class EducationFacilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_education_facility(self, facility_data: Dict) -> EducationFacility:
        facility = EducationFacility(**facility_data)
        self.db.add(facility)
        self.db.commit()
        self.db.refresh(facility)
        return facility

    def get_education_facility_by_id(self, facility_id: int) -> Optional[EducationFacility]:
        return self.db.query(EducationFacility).filter(
            EducationFacility.id == facility_id, 
            EducationFacility.is_deleted == False
        ).first()

    def get_education_facility_by_name(self, name: str) -> Optional[EducationFacility]:
        return self.db.query(EducationFacility).filter(
            EducationFacility.name == name,
            EducationFacility.is_deleted == False
        ).first()

    def get_all_education_facilities(self, skip: int = 0, limit: int = 100) -> List[EducationFacility]:
        return self.db.query(EducationFacility).filter(
            EducationFacility.is_deleted == False
        ).offset(skip).limit(limit).all()

    def search_education_facilities(self, search_term: str, skip: int = 0, limit: int = 100) -> List[EducationFacility]:
        return self.db.query(EducationFacility).filter(
            EducationFacility.name.ilike(f"%{search_term}%"),
            EducationFacility.is_deleted == False
        ).offset(skip).limit(limit).all()

    def update_education_facility(self, facility_id: int, update_data: Dict) -> Optional[EducationFacility]:
        facility = self.get_education_facility_by_id(facility_id)
        if facility:
            for key, value in update_data.items():
                if hasattr(facility, key):
                    setattr(facility, key, value)
            self.db.commit()
            self.db.refresh(facility)
        return facility

    def delete_education_facility(self, facility_id: int) -> bool:
        facility = self.get_education_facility_by_id(facility_id)
        if facility:
            facility.is_deleted = True
            self.db.commit()
            return True
        return False

    def get_education_facilities_by_country(self, country: str, skip: int = 0, limit: int = 100) -> List[EducationFacility]:
        return self.db.query(EducationFacility).filter(
            EducationFacility.country == country,
            EducationFacility.is_deleted == False
        ).offset(skip).limit(limit).all()
