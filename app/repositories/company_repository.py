from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.company import Company
from .base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Company)
    
    def create_company(self, data: Dict) -> Company:
        """Create a new company"""
        return self.create(data)
    
    def get_company_by_id(self, id: int) -> Optional[Company]:
        """Get company by ID (excluding deleted)"""
        return self.get_by_id(id, include_deleted=False)
    
    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get company by name (excluding deleted)"""
        companies = self.search("name", name, case_sensitive=False)
        return companies[0] if companies else None
    
    def get_all_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get all companies with pagination (excluding deleted)"""
        return self.get_all(skip=skip, limit=limit, include_deleted=False)
    
    def update_company(self, id: int, update_data: Dict) -> Optional[Company]:
        """Update company"""
        return self.update(id, update_data, exclude_unset=False)
    
    def delete_company(self, id: int) -> bool:
        """Soft delete company"""
        return self.delete(id, hard_delete=False)
    
    def search_companies(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Company]:
        """Search companies by name"""
        return self.search("name", search_term, skip=skip, limit=limit, case_sensitive=False)
