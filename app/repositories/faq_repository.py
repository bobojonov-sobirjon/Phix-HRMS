from sqlalchemy.orm import Session
from app.models.faq import FAQ
from app.schemas.faq import FAQCreate, FAQUpdate

class FAQRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(FAQ).all()

    @staticmethod
    def get_by_id(db: Session, faq_id: int):
        return db.query(FAQ).filter(FAQ.id == faq_id).first()

    @staticmethod
    def create(db: Session, faq: FAQCreate):
        db_faq = FAQ(**faq.dict())
        db.add(db_faq)
        db.commit()
        db.refresh(db_faq)
        return db_faq

    @staticmethod
    def update(db: Session, faq_id: int, faq: FAQUpdate):
        db_faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not db_faq:
            return None
        for var, value in faq.dict(exclude_unset=True).items():
            setattr(db_faq, var, value)
        db.commit()
        db.refresh(db_faq)
        return db_faq

    @staticmethod
    def delete(db: Session, faq_id: int):
        db_faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not db_faq:
            return None
        db.delete(db_faq)
        db.commit()
        return db_faq 