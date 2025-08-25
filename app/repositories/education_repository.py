from sqlalchemy.orm import Session, selectinload
from typing import List, Optional, Dict
from ..models.education import Education
from ..schemas.profile import EducationCreate
from ..models.education_facility import EducationFacility

class EducationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_education(self, user_id: int, education_data: EducationCreate) -> Education:
        edu_data = education_data.dict()
        
        # school_name yuborilgan bo'lsa, avtomatik facility yaratish
        if education_data.school_name:
            facility_name = education_data.school_name
            # Check if facility already exists using partial matching
            # First try exact match
            facility = self.db.query(EducationFacility).filter(EducationFacility.name == facility_name).first()
            if not facility:
                # Then try partial match (facility_name is contained in existing facility name)
                facility = self.db.query(EducationFacility).filter(EducationFacility.name.contains(facility_name)).first()
            if not facility:
                # Finally try reverse partial match (existing facility name is contained in facility_name)
                facility = self.db.query(EducationFacility).filter(EducationFacility.name.op('LIKE')(f'%{facility_name}%')).first()
            if not facility:
                # Create new facility only if no match found
                facility = EducationFacility(name=facility_name, icon=None)
                self.db.add(facility)
                self.db.commit()
                self.db.refresh(facility)
            # school_name orqali topilgan facility ID'sini education_facility_id ga o'rnatish
            edu_data['education_facility_id'] = facility.id
            edu_data.pop('school_name', None)
        elif education_data.education_facility_id:
            # education_facility_id to'g'ridan-to'g'ri yuborilgan
            # Facility mavjudligini tekshirish
            facility = self.db.query(EducationFacility).filter(EducationFacility.id == education_data.education_facility_id).first()
            if not facility:
                raise ValueError(f"Education facility with ID {education_data.education_facility_id} not found")
        else:
            raise ValueError("Either school_name or education_facility_id must be provided")
        
        try:
            education = Education(user_id=user_id, **edu_data)
            self.db.add(education)
            self.db.commit()
            self.db.refresh(education)
            return education
        except Exception as e:
            self.db.rollback()
            raise e

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
            # school_name yuborilgan bo'lsa, avtomatik facility yaratish
            if 'school_name' in update_data and update_data['school_name']:
                facility_name = update_data['school_name']
                # Check if facility already exists using partial matching
                # First try exact match
                facility = self.db.query(EducationFacility).filter(EducationFacility.name == facility_name).first()
                if not facility:
                    # Then try partial match (facility_name is contained in existing facility name)
                    facility = self.db.query(EducationFacility).filter(EducationFacility.name.contains(facility_name)).first()
                if not facility:
                    # Finally try reverse partial match (existing facility name is contained in facility_name)
                    facility = self.db.query(EducationFacility).filter(EducationFacility.name.op('LIKE')(f'%{facility_name}%')).first()
                if not facility:
                    # Create new facility only if no match found
                    facility = EducationFacility(name=facility_name, icon=None)
                    self.db.add(facility)
                    self.db.commit()
                    self.db.refresh(facility)
                update_data['education_facility_id'] = facility.id
                update_data.pop('school_name')
            
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