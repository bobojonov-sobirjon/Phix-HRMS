from sqlalchemy.orm import Session
from app.models.faq import FAQ
from app.schemas.faq import FAQCreate, FAQUpdate
from .base_repository import BaseRepository


class FAQRepository(BaseRepository[FAQ]):
    """Repository for FAQ model"""
    
    def __init__(self, db: Session):
        super().__init__(db, FAQ)
    
    @staticmethod
    def get_all(db: Session):
        """Get all FAQs (static method for backward compatibility)"""
        repo = FAQRepository(db)
        return repo.get_all(include_deleted=False)
    
    @staticmethod
    def get_by_id(db: Session, faq_id: int):
        """Get FAQ by ID (static method for backward compatibility)"""
        repo = FAQRepository(db)
        return repo.get_by_id(faq_id, include_deleted=False)
    
    @staticmethod
    def create(db: Session, faq: FAQCreate):
        """Create FAQ (static method for backward compatibility)"""
        repo = FAQRepository(db)
        return repo.create(faq.dict())
    
    @staticmethod
    def update(db: Session, faq_id: int, faq: FAQUpdate):
        """Update FAQ (static method for backward compatibility)"""
        repo = FAQRepository(db)
        return repo.update(faq_id, faq, exclude_unset=True)
    
    @staticmethod
    def delete(db: Session, faq_id: int):
        """Delete FAQ (static method for backward compatibility)"""
        repo = FAQRepository(db)
        success = repo.delete(faq_id, hard_delete=True)
        if success:
            return repo.get_by_id(faq_id, include_deleted=True)
        return None
