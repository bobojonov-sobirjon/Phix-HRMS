from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.company_repository import CompanyRepository
from ..schemas.profile import CompanyResponse, CompanyCreate, CompanyUpdate
from ..schemas.common import SuccessResponse
from ..utils.decorators import handle_errors
from ..utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    validate_entity_exists
)
from typing import List

router = APIRouter(prefix="/companies", tags=["Companies"])

@router.get("/", response_model=SuccessResponse, tags=["Companies"])
@handle_errors
async def get_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all companies with optional search and pagination"""
    repo = CompanyRepository(db)
    if search:
        companies = repo.search_companies(search, skip, limit)
    else:
        companies = repo.get_all_companies(skip, limit)
    
    company_responses = [CompanyResponse.model_validate(company) for company in companies]
    return success_response(
        data=company_responses,
        message="Companies retrieved successfully"
    )

@router.get("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
@handle_errors
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific company by ID"""
    repo = CompanyRepository(db)
    company = repo.get_company_by_id(company_id)
    validate_entity_exists(company, "Company")
    
    company_response = CompanyResponse.model_validate(company)
    return success_response(
        data=company_response,
        message="Company retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse, tags=["Companies"])
@handle_errors
async def create_company(
    company: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new company"""
    repo = CompanyRepository(db)
    
    # Check if company with same name already exists
    existing_company = repo.get_company_by_name(company.name)
    if existing_company:
        raise bad_request_error("Company with this name already exists")
    
    created_company = repo.create_company(company.dict())
    company_response = CompanyResponse.model_validate(created_company)
    
    return success_response(
        data=company_response,
        message="Company created successfully"
    )

@router.patch("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
@handle_errors
async def update_company(
    company_id: int,
    company: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing company"""
    repo = CompanyRepository(db)
    
    # Check if company exists
    existing_company = repo.get_company_by_id(company_id)
    validate_entity_exists(existing_company, "Company")
    
    # If updating name, check for duplicates
    if company.name and company.name != existing_company.name:
        duplicate_company = repo.get_company_by_name(company.name)
        if duplicate_company:
            raise bad_request_error("Company with this name already exists")
    
    updated_company = repo.update_company(company_id, company.dict(exclude_unset=True))
    company_response = CompanyResponse.model_validate(updated_company)
    
    return success_response(
        data=company_response,
        message="Company updated successfully"
    )

@router.delete("/{company_id}", response_model=SuccessResponse, tags=["Companies"])
@handle_errors
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a company (soft delete)"""
    repo = CompanyRepository(db)
    
    # Check if company exists
    existing_company = repo.get_company_by_id(company_id)
    validate_entity_exists(existing_company, "Company")
    
    if not repo.delete_company(company_id):
        raise bad_request_error("Failed to delete company")
    
    return success_response(
        data=None,
        message="Company deleted successfully"
    )
