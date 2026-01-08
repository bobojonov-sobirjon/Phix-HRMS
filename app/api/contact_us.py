from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.contact_us import ContactUsCreate, ContactUsUpdate, ContactUsOut
from app.schemas.common import SuccessResponse
from app.repositories.contact_us_repository import ContactUsRepository
from app.utils.decorators import handle_errors
from app.utils.response_helpers import success_response, not_found_error, validate_entity_exists

router = APIRouter(prefix="/contact-us", tags=["Contact Us"])

@router.get("/", response_model=SuccessResponse)
@handle_errors
async def get_contacts(db: Session = Depends(get_db)):
    """Get all contacts"""
    contacts = ContactUsRepository.get_all(db)
    contact_schemas = [ContactUsOut.model_validate(contact) for contact in contacts]
    return success_response(
        data=contact_schemas,
        message="Contacts retrieved successfully"
    )

@router.get("/{contact_id}", response_model=SuccessResponse)
@handle_errors
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get contact by ID"""
    contact = ContactUsRepository.get_by_id(db, contact_id)
    validate_entity_exists(contact, "Contact")
    contact_schema = ContactUsOut.model_validate(contact)
    return success_response(
        data=contact_schema,
        message="Contact retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse)
@handle_errors
async def create_contact(contact: ContactUsCreate, db: Session = Depends(get_db)):
    """Create a new contact"""
    created_contact = ContactUsRepository.create(db, contact)
    contact_schema = ContactUsOut.model_validate(created_contact)
    return success_response(
        data=contact_schema,
        message="Contact created successfully"
    )

@router.put("/{contact_id}", response_model=SuccessResponse)
@handle_errors
async def update_contact(contact_id: int, contact: ContactUsUpdate, db: Session = Depends(get_db)):
    """Update contact"""
    updated = ContactUsRepository.update(db, contact_id, contact)
    validate_entity_exists(updated, "Contact")
    contact_schema = ContactUsOut.model_validate(updated)
    return success_response(
        data=contact_schema,
        message="Contact updated successfully"
    )

@router.delete("/{contact_id}", response_model=SuccessResponse)
@handle_errors
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete contact"""
    deleted = ContactUsRepository.delete(db, contact_id)
    if not deleted:
        raise not_found_error("Contact not found")
    contact_schema = ContactUsOut.model_validate(deleted)
    return success_response(
        data=contact_schema,
        message="Contact deleted successfully"
    ) 
    