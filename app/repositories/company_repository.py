from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.company import Company

class CompanyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_company(self, data: Dict) -> Company:
        company = Company(**data)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def get_company_by_id(self, id: int) -> Optional[Company]:
        return self.db.query(Company).filter(Company.id == id, Company.is_deleted == False).first()

    def get_company_by_name(self, name: str) -> Optional[Company]:
        return self.db.query(Company).filter(Company.name == name, Company.is_deleted == False).first()

    def get_all_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        return self.db.query(Company).filter(Company.is_deleted == False).offset(skip).limit(limit).all()

    def update_company(self, id: int, update_data: Dict) -> Optional[Company]:
        company = self.get_company_by_id(id)
        if company:
            for k, v in update_data.items():
                setattr(company, k, v)
            self.db.commit()
            self.db.refresh(company)
        return company

    def delete_company(self, id: int) -> bool:
        company = self.get_company_by_id(id)
        if company:
            company.is_deleted = True
            self.db.commit()
            return True
        return False

    def search_companies(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Company]:
        return self.db.query(Company).filter(
            Company.is_deleted == False,
            Company.name.ilike(f"%{search_term}%")
        ).offset(skip).limit(limit).all()
