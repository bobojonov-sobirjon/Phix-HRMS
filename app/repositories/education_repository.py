from sqlalchemy.orm import Session, selectinload
from typing import List, Optional, Dict
from ..models.education import Education
from ..schemas.profile import EducationCreate
from ..models.education_facility import EducationFacility

class EducationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_education(self, user_id: int, education_data: EducationCreate) -> Education:
        facility_name = education_data.school_name if hasattr(education_data, 'school_name') else None
        facility_id = None
        if facility_name:
            facility = self.db.query(EducationFacility).filter(EducationFacility.name == facility_name).first()
            if not facility:
                facility = EducationFacility(name=facility_name, icon=None)
                self.db.add(facility)
                self.db.commit()
                self.db.refresh(facility)
            facility_id = facility.id
        edu_data = education_data.dict()
        edu_data.pop('school_name', None)
        edu_data['education_facility_id'] = facility_id
        education = Education(user_id=user_id, **edu_data)
        self.db.add(education)
        self.db.commit()
        self.db.refresh(education)
        return education

    def get_education_by_id(self, education_id: int) -> Optional[Education]:
        return self.db.query(Education).options(
            selectinload(Education.education_facility)
        ).filter(Education.id == education_id, Education.is_deleted == False).first()

    def get_educations_by_user(self, user_id: int) -> List[Education]:
        return self.db.query(Education).options(
            selectinload(Education.education_facility)
        ).filter(Education.user_id == user_id, Education.is_deleted == False).all()

    def update_education(self, education_id: int, update_data: Dict) -> Optional[Education]:
        education = self.get_education_by_id(education_id)
        if education:
            for key, value in update_data.items():
                setattr(education, key, value)
            self.db.commit()
            self.db.refresh(education)
        return education

    def delete_education(self, education_id: int, user_id: int) -> bool:
        education = self.get_education_by_id(education_id)
        if education and education.user_id == user_id:
            education.is_deleted = True
            self.db.commit()
            return True
        return False 