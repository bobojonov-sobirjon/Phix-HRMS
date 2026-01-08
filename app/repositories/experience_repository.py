from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.experience import Experience
from ..schemas.profile import ExperienceCreate
from ..models.company import Company

class ExperienceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_experience(self, user_id: int, data: ExperienceCreate) -> Experience:
        if hasattr(data, 'model_dump'):
            exp_data = data.model_dump(exclude_unset=True)
        else:
            exp_data = data.dict(exclude_unset=True)
        
        company_name = exp_data.get('company_name') or (data.company_name if hasattr(data, 'company_name') and data.company_name else None)
        company_id = None
        
        if company_name:
            try:
                company = self.db.query(Company).filter(Company.name == company_name, Company.is_deleted == False).first()
                if not company:
                    company = self.db.query(Company).filter(Company.name.contains(company_name), Company.is_deleted == False).first()
                if not company:
                    company = self.db.query(Company).filter(Company.name.op('LIKE')(f'%{company_name}%'), Company.is_deleted == False).first()
                if not company:
                    company = Company(name=company_name, icon=None)
                    self.db.add(company)
                    self.db.flush()
                    self.db.refresh(company)
                company_id = company.id
            except Exception as e:
                from ..core.logging_config import logger
                logger.error(f"Error processing company_name in create_experience: {e}", exc_info=True)
        
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
        if not exp:
            return None
        
        try:
            company_name = update_data.pop('company_name', None)
            if company_name:
                try:
                    company = self.db.query(Company).filter(Company.name == company_name, Company.is_deleted == False).first()
                    if not company:
                        company = self.db.query(Company).filter(Company.name.contains(company_name), Company.is_deleted == False).first()
                    if not company:
                        company = self.db.query(Company).filter(Company.name.op('LIKE')(f'%{company_name}%'), Company.is_deleted == False).first()
                    if not company:
                        company = Company(name=company_name, icon=None)
                        self.db.add(company)
                        self.db.flush()
                        self.db.refresh(company)
                    exp.company_id = company.id
                except Exception as e:
                    from ..core.logging_config import logger
                    logger.error(f"Error processing company_name in update_experience: {e}", exc_info=True)
            
            for k, v in update_data.items():
                if hasattr(exp, k):
                    setattr(exp, k, v)
            
            self.db.commit()
            self.db.refresh(exp)
            return exp
        except Exception as e:
            self.db.rollback()
            from ..core.logging_config import logger
            logger.error(f"Error updating experience: {e}", exc_info=True)
            raise

    def delete_experience(self, id: int, user_id: int) -> bool:
        exp = self.get_experience_by_id(id)
        if exp and exp.user_id == user_id:
            exp.is_deleted = True
            self.db.commit()
            return True
        return False 