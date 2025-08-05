from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.faq import FAQCreate, FAQUpdate, FAQOut
from app.repositories.faq_repository import FAQRepository
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/faq", tags=["FAQ"])

@router.get("/", response_model=SuccessResponse)
def get_faqs(db: Session = Depends(get_db)):
    try:
        faqs = FAQRepository.get_all(db)
        # Convert SQLAlchemy models to Pydantic schemas
        faq_schemas = [FAQOut.model_validate(faq) for faq in faqs]
        return SuccessResponse(
            msg="FAQs retrieved successfully",
            data=faq_schemas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{faq_id}", response_model=SuccessResponse)
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    try:
        faq = FAQRepository.get_by_id(db, faq_id)
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        # Convert SQLAlchemy model to Pydantic schema
        faq_schema = FAQOut.model_validate(faq)
        return SuccessResponse(
            msg="FAQ retrieved successfully",
            data=faq_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse)
def create_faq(faq: FAQCreate, db: Session = Depends(get_db)):
    try:
        created_faq = FAQRepository.create(db, faq)
        # Convert SQLAlchemy model to Pydantic schema
        faq_schema = FAQOut.model_validate(created_faq)
        return SuccessResponse(
            msg="FAQ created successfully",
            data=faq_schema
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{faq_id}", response_model=SuccessResponse)
def update_faq(faq_id: int, faq: FAQUpdate, db: Session = Depends(get_db)):
    try:
        updated = FAQRepository.update(db, faq_id, faq)
        if not updated:
            raise HTTPException(status_code=404, detail="FAQ not found")
        # Convert SQLAlchemy model to Pydantic schema
        faq_schema = FAQOut.model_validate(updated)
        return SuccessResponse(
            msg="FAQ updated successfully",
            data=faq_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{faq_id}", response_model=SuccessResponse)
def delete_faq(faq_id: int, db: Session = Depends(get_db)):
    try:
        deleted = FAQRepository.delete(db, faq_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="FAQ not found")
        # Convert SQLAlchemy model to Pydantic schema
        faq_schema = FAQOut.model_validate(deleted)
        return SuccessResponse(
            msg="FAQ deleted successfully",
            data=faq_schema
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 