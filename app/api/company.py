from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.company_repository import CompanyRepository
from ..schemas.profile import CompanyResponse, CompanyCreate, CompanyUpdate
from ..schemas.common import SuccessResponse, ErrorResponse
from typing import List

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/", response_model=SuccessResponse, tags=["Companies"])
def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all companies with optional search and pagination"""
    try:
        repo = CompanyRepository(db)
        if search:
            companies = repo.search_companies(search, skip, limit)
        else:
            companies = repo.get_all_companies(skip, limit)
        
        company_responses = [CompanyResponse.model_validate(company) for company in companies]
        return SuccessResponse(
            msg="Companies retrieved successfully",
            data=company_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific company by ID"""
    try:
        repo = CompanyRepository(db)
        company = repo.get_company_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_response = CompanyResponse.model_validate(company)
        return SuccessResponse(
            msg="Company retrieved successfully",
            data=company_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse, tags=["Companies"])
def create_company(
    company: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new company"""
    try:
        repo = CompanyRepository(db)
        
        # Check if company with same name already exists
        existing_company = repo.get_company_by_name(company.name)
        if existing_company:
            raise HTTPException(status_code=400, detail="Company with this name already exists")
        
        created_company = repo.create_company(company.dict())
        company_response = CompanyResponse.model_validate(created_company)
        
        return SuccessResponse(
            msg="Company created successfully",
            data=company_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
def update_company(
    company_id: int,
    company: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing company"""
    try:
        repo = CompanyRepository(db)
        
        # Check if company exists
        existing_company = repo.get_company_by_id(company_id)
        if not existing_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # If updating name, check for duplicates
        if company.name and company.name != existing_company.name:
            duplicate_company = repo.get_company_by_name(company.name)
            if duplicate_company:
                raise HTTPException(status_code=400, detail="Company with this name already exists")
        
        updated_company = repo.update_company(company_id, company.dict(exclude_unset=True))
        company_response = CompanyResponse.model_validate(updated_company)
        
        return SuccessResponse(
            msg="Company updated successfully",
            data=company_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a company (soft delete)"""
    try:
        repo = CompanyRepository(db)
        
        # Check if company exists
        existing_company = repo.get_company_by_id(company_id)
        if not existing_company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        if not repo.delete_company(company_id):
            raise HTTPException(status_code=500, detail="Failed to delete company")
        
        return SuccessResponse(msg="Company deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
