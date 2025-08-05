from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.contact_us import ContactUsCreate, ContactUsUpdate, ContactUsOut
from app.repositories.contact_us_repository import ContactUsRepository
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/contact-us", tags=["Contact Us"])

@router.get("/", response_model=SuccessResponse)
def get_contacts(db: Session = Depends(get_db)):
    try:
        contacts = ContactUsRepository.get_all(db)
        # Convert SQLAlchemy models to Pydantic schemas
        contact_schemas = [ContactUsOut.model_validate(contact) for contact in contacts]
        return SuccessResponse(
            msg="Contacts retrieved successfully",
            data=contact_schemas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{contact_id}", response_model=SuccessResponse)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    try:
        contact = ContactUsRepository.get_by_id(db, contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        # Convert SQLAlchemy model to Pydantic schema
        contact_schema = ContactUsOut.model_validate(contact)
        return SuccessResponse(
            msg="Contact retrieved successfully",
            data=contact_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse)
def create_contact(contact: ContactUsCreate, db: Session = Depends(get_db)):
    try:
        created_contact = ContactUsRepository.create(db, contact)
        # Convert SQLAlchemy model to Pydantic schema
        contact_schema = ContactUsOut.model_validate(created_contact)
        return SuccessResponse(
            msg="Contact created successfully",
            data=contact_schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{contact_id}", response_model=SuccessResponse)
def update_contact(contact_id: int, contact: ContactUsUpdate, db: Session = Depends(get_db)):
    try:
        updated = ContactUsRepository.update(db, contact_id, contact)
        if not updated:
            raise HTTPException(status_code=404, detail="Contact not found")
        # Convert SQLAlchemy model to Pydantic schema
        contact_schema = ContactUsOut.model_validate(updated)
        return SuccessResponse(
            msg="Contact updated successfully",
            data=contact_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{contact_id}", response_model=SuccessResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    try:
        deleted = ContactUsRepository.delete(db, contact_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Contact not found")
        # Convert SQLAlchemy model to Pydantic schema
        contact_schema = ContactUsOut.model_validate(deleted)
        return SuccessResponse(
            msg="Contact deleted successfully",
            data=contact_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    