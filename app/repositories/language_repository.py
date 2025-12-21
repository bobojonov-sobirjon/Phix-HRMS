from sqlalchemy.orm import Session
from ..models.language import Language
from typing import Optional, List
from .base_repository import BaseRepository


class LanguageRepository(BaseRepository[Language]):
    """Repository for Language model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Language)
    
    def get(self, language_id: int) -> Optional[Language]:
        """Get language by ID"""
        return self.get_by_id(language_id, include_deleted=False)
    
    def get_all(self) -> List[Language]:
        """Get all languages"""
        return self.get_all(include_deleted=False)
    
    def create(self, name: str) -> Language:
        """Create a new language"""
        return self.create({"name": name})
    
    def update(self, language_id: int, name: str) -> Optional[Language]:
        """Update language"""
        return self.update(language_id, {"name": name}, exclude_unset=False)
    
    def delete(self, language_id: int) -> bool:
        """Hard delete language (languages don't have is_deleted)"""
        return super().delete(language_id, hard_delete=True)
    
    def get_language_by_id(self, language_id: int) -> Optional[Language]:
        """Get language by ID (alias for get)"""
        return self.get(language_id)
    
    def get_all_languages(self) -> List[Language]:
        """Get all languages (alias for get_all)"""
        return self.get_all()
    
    def create_language(self, name: str) -> Language:
        """Create a new language (alias for create)"""
        return self.create(name)
    
    def update_language(self, language_id: int, name: str) -> Optional[Language]:
        """Update language (alias for update)"""
        return self.update(language_id, name)
