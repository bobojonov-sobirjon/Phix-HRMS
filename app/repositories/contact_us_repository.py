from sqlalchemy.orm import Session
from app.models.contact_us import ContactUs
from app.schemas.contact_us import ContactUsCreate, ContactUsUpdate

class ContactUsRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(ContactUs).all()

    @staticmethod
    def get_by_id(db: Session, contact_id: int):
        return db.query(ContactUs).filter(ContactUs.id == contact_id).first()

    @staticmethod
    def create(db: Session, contact: ContactUsCreate):
        db_contact = ContactUs(**contact.dict())
        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def update(db: Session, contact_id: int, contact: ContactUsUpdate):
        db_contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
        if not db_contact:
            return None
        for var, value in contact.dict(exclude_unset=True).items():
            setattr(db_contact, var, value)
        db.commit()
        db.refresh(db_contact)
        return db_contact

    @staticmethod
    def delete(db: Session, contact_id: int):
        db_contact = db.query(ContactUs).filter(ContactUs.id == contact_id).first()
        if not db_contact:
            return None
        db.delete(db_contact)
        db.commit()
        return db_contact 