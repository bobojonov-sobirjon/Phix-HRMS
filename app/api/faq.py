from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.repositories.faq_repository import FAQRepository

router = APIRouter(prefix="/faq", tags=["FAQ"])

@router.get("/", response_model=List[FAQOut])
def get_faqs(db: Session = Depends(get_db)):
    return FAQRepository.get_all(db)

@router.get("/{faq_id}", response_model=FAQOut)
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = FAQRepository.get_by_id(db, faq_id)
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return faq

@router.post("/", response_model=FAQOut)
def create_faq(faq: FAQCreate, db: Session = Depends(get_db)):
    return FAQRepository.create(db, faq)

@router.put("/{faq_id}", response_model=FAQOut)
def update_faq(faq_id: int, faq: FAQUpdate, db: Session = Depends(get_db)):
    updated = FAQRepository.update(db, faq_id, faq)
    if not updated:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return updated

@router.delete("/{faq_id}", response_model=FAQOut)
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    deleted = FAQRepository.delete(db, faq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return deleted 