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
        # Call base repository's get_all method directly using instance
        return BaseRepository.get_all(repo, skip=0, limit=1000, include_deleted=False)
    
    @staticmethod
    def get_by_id(db: Session, faq_id: int):
        """Get FAQ by ID (static method for backward compatibility)"""
        repo = FAQRepository(db)
        return repo.get_by_id(faq_id, include_deleted=False)
    
    @staticmethod
    def create(db: Session, faq: FAQCreate):
        """Create FAQ (static method for backward compatibility)"""
        repo = FAQRepository(db)
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        faq_dict = faq.model_dump() if hasattr(faq, 'model_dump') else faq.dict()
        return repo.create(faq_dict)
    
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
