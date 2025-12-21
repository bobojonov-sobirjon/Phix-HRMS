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
        # Call the base class instance method explicitly
        return BaseRepository.get_all(repo, include_deleted=False)
    
    @staticmethod
    def get_by_id(db: Session, contact_id: int):
        """Get contact by ID (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        # Call the base class instance method explicitly
        return BaseRepository.get_by_id(repo, contact_id, include_deleted=False)
    
    @staticmethod
    def create(db: Session, contact: ContactUsCreate):
        """Create contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        # Convert Pydantic model to dict (support both v1 and v2)
        if hasattr(contact, 'model_dump'):
            contact_dict = contact.model_dump()
        else:
            contact_dict = contact.dict()
        # Call the base class instance method explicitly
        return BaseRepository.create(repo, contact_dict)
    
    @staticmethod
    def update(db: Session, contact_id: int, contact: ContactUsUpdate):
        """Update contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        # BaseRepository.update() handles Pydantic models automatically
        # Call the base class instance method explicitly
        return BaseRepository.update(repo, contact_id, contact, exclude_unset=True)
    
    @staticmethod
    def delete(db: Session, contact_id: int):
        """Delete contact (static method for backward compatibility)"""
        repo = ContactUsRepository(db)
        # Get the contact before deleting it (for hard delete, we need to return it)
        contact = BaseRepository.get_by_id(repo, contact_id, include_deleted=False)
        if not contact:
            return None
        # Call the base class instance method explicitly
        success = BaseRepository.delete(repo, contact_id, hard_delete=True)
        if success:
            # Return the contact that was deleted (we already have it)
            return contact
        return None
