from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.schemas.common import SuccessResponse
from app.repositories.faq_repository import FAQRepository
from app.utils.decorators import handle_errors
from app.utils.response_helpers import success_response, not_found_error, validate_entity_exists

router = APIRouter(prefix="/faq", tags=["FAQ"])

@router.get("/", response_model=SuccessResponse)
@handle_errors
async def get_faqs(db: Session = Depends(get_db)):
    """Get all FAQs"""
    faqs = FAQRepository.get_all(db)
    # Convert SQLAlchemy models to Pydantic schemas
    faq_schemas = [FAQOut.model_validate(faq) for faq in faqs]
    return success_response(
        data=faq_schemas,
        message="FAQs retrieved successfully"
    )

@router.get("/{faq_id}", response_model=SuccessResponse)
@handle_errors
async def get_faq(faq_id: int, db: Session = Depends(get_db)):
    """Get FAQ by ID"""
    faq = FAQRepository.get_by_id(db, faq_id)
    validate_entity_exists(faq, "FAQ")
    # Convert SQLAlchemy model to Pydantic schema
    faq_schema = FAQOut.model_validate(faq)
    return success_response(
        data=faq_schema,
        message="FAQ retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse)
@handle_errors
async def create_faq(faq: FAQCreate, db: Session = Depends(get_db)):
    """Create a new FAQ"""
    created_faq = FAQRepository.create(db, faq)
    # Convert SQLAlchemy model to Pydantic schema
    faq_schema = FAQOut.model_validate(created_faq)
    return success_response(
        data=faq_schema,
        message="FAQ created successfully"
    )

@router.put("/{faq_id}", response_model=SuccessResponse)
@handle_errors
async def update_faq(faq_id: int, faq: FAQUpdate, db: Session = Depends(get_db)):
    """Update FAQ"""
    updated = FAQRepository.update(db, faq_id, faq)
    validate_entity_exists(updated, "FAQ")
    # Convert SQLAlchemy model to Pydantic schema
    faq_schema = FAQOut.model_validate(updated)
    return success_response(
        data=faq_schema,
        message="FAQ updated successfully"
    )

@router.delete("/{faq_id}", response_model=SuccessResponse)
@handle_errors
async def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    """Delete FAQ"""
    deleted = FAQRepository.delete(db, faq_id)
    if not deleted:
        raise not_found_error("FAQ not found")
    # Convert SQLAlchemy model to Pydantic schema
    faq_schema = FAQOut.model_validate(deleted)
    return success_response(
        data=faq_schema,
        message="FAQ deleted successfully"
    ) 