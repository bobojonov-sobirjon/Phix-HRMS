from sqlalchemy.orm import Session
from app.models.contact_us import ContactUs
from app.schemas.contact_us import ContactUsCreate, ContactUsUpdate
from .base_repository import BaseRepository


class ContactUsRepository(BaseRepository[ContactUs]):
    """Repository for ContactUs model"""
    
    def __init__(self, db: Session):
        super().__init__(db, ContactUs)
    
    @staticmethod
    def get_all(db: Session):
        """Get all contacts (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        return BaseRepository.get_all(repo, include_deleted=False)
    
    @staticmethod
    def get_by_id(db: Session, contact_id: int):
        """Get contact by ID (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        return BaseRepository.get_by_id(repo, contact_id, include_deleted=False)
    
    @staticmethod
    def create(db: Session, contact: ContactUsCreate):
        """Create contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        if hasattr(contact, 'model_dump'):
            contact_dict = contact.model_dump()
        else:
            contact_dict = contact.dict()
        return BaseRepository.create(repo, contact_dict)
    
    @staticmethod
    def update(db: Session, contact_id: int, contact: ContactUsUpdate):
        """Update contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        return BaseRepository.update(repo, contact_id, contact, exclude_unset=True)
    
    @staticmethod
    def delete(db: Session, contact_id: int):
        """Delete contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        contact = BaseRepository.get_by_id(repo, contact_id, include_deleted=False)
        if not contact:
            return None
        success = BaseRepository.delete(repo, contact_id, hard_delete=True)
        if success:
            return contact
        return None
