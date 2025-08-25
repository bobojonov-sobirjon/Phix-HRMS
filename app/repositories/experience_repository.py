from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.experience import Experience
from ..schemas.profile import ExperienceCreate
from ..models.company import Company

class ExperienceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_experience(self, user_id: int, data: ExperienceCreate) -> Experience:
        company_name = data.company_name if hasattr(data, 'company_name') else None
        company_id = None
        if company_name:
            # Check if company already exists using partial matching
            # First try exact match
            company = self.db.query(Company).filter(Company.name == company_name).first()
            if not company:
                # Then try partial match (company_name is contained in existing company name)
                company = self.db.query(Company).filter(Company.name.contains(company_name)).first()
            if not company:
                # Finally try reverse partial match (existing company name is contained in company_name)
                company = self.db.query(Company).filter(Company.name.op('LIKE')(f'%{company_name}%')).first()
            if not company:
                # Create new company only if no match found
                company = Company(name=company_name, icon=None)
                self.db.add(company)
                self.db.commit()
                self.db.refresh(company)
            company_id = company.id
        
        exp_data = data.dict()
        exp_data.pop('company_name', None)
        exp_data['company_id'] = company_id
        exp = Experience(user_id=user_id, **exp_data)
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)
        return exp

    def get_experience_by_id(self, id: int) -> Optional[Experience]:
        return self.db.query(Experience).filter(Experience.id == id, Experience.is_deleted == False).first()

    def get_experiences_by_user(self, user_id: int) -> List[Experience]:
        return self.db.query(Experience).filter(Experience.user_id == user_id, Experience.is_deleted == False).all()

    def update_experience(self, id: int, update_data: Dict) -> Optional[Experience]:
        exp = self.get_experience_by_id(id)
        if exp:
            # Handle company_name update separately
            company_name = update_data.pop('company_name', None)
            if company_name:
                # Check if company exists using partial matching
                # First try exact match
                company = self.db.query(Company).filter(Company.name == company_name).first()
                if not company:
                    # Then try partial match (company_name is contained in existing company name)
                    company = self.db.query(Company).filter(Company.name.contains(company_name)).first()
                if not company:
                    # Finally try reverse partial match (existing company name is contained in company_name)
                    company = self.db.query(Company).filter(Company.name.op('LIKE')(f'%{company_name}%')).first()
                if not company:
                    # Create new company if no match found
                    company = Company(name=company_name, icon=None)
                    self.db.add(company)
                    self.db.commit()
                    self.db.refresh(company)
                # Update company_id
                exp.company_id = company.id
            
            # Update other fields
            for k, v in update_data.items():
                setattr(exp, k, v)
            
            self.db.commit()
            self.db.refresh(exp)
        return exp

    def delete_experience(self, id: int, user_id: int) -> bool:
        exp = self.get_experience_by_id(id)
        if exp and exp.user_id == user_id:
            exp.is_deleted = True
            self.db.commit()
            return True
        return False 