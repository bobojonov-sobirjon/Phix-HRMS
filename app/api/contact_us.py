from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.contact_us import ContactUsCreate, ContactUsUpdate, ContactUsOut
from app.repositories.contact_us_repository import ContactUsRepository

router = APIRouter(prefix="/contact-us", tags=["Contact Us"])

@router.get("/", response_model=List[ContactUsOut])
def get_contacts(db: Session = Depends(get_db)):
    return ContactUsRepository.get_all(db)

@router.get("/{contact_id}", response_model=ContactUsOut)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = ContactUsRepository.get_by_id(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@router.post("/", response_model=ContactUsOut)
def create_contact(contact: ContactUsCreate, db: Session = Depends(get_db)):
    return ContactUsRepository.create(db, contact)

@router.put("/{contact_id}", response_model=ContactUsOut)
def update_contact(contact_id: int, contact: ContactUsUpdate, db: Session = Depends(get_db)):
    updated = ContactUsRepository.update(db, contact_id, contact)
    if not updated:
        raise HTTPException(status_code=404, detail="Contact not found")
    return updated

@router.delete("/{contact_id}", response_model=ContactUsOut)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    deleted = ContactUsRepository.delete(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")
    return deleted 