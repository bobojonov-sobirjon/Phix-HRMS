from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..repositories.role_repository import RoleRepository
from ..utils.decorators import handle_errors
from ..utils.response_helpers import success_response, not_found_error, bad_request_error, validate_entity_exists
from ..schemas.common import SuccessResponse
from pydantic import BaseModel

class RoleCreate(BaseModel):
    name: str

class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

router = APIRouter(prefix='/roles', tags=['Roles'])

@router.post('/', response_model=SuccessResponse)
@handle_errors
async def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    """Create a new role"""
    repo = RoleRepository(db)
    existing = repo.get_role_by_name(role_data.name)
    if existing:
        raise bad_request_error('Role already exists')
    role = repo.create_role(role_data.name)
    role_response = RoleResponse.model_validate(role)
    return success_response(
        data=role_response,
        message="Role created successfully"
    )

@router.get('/', response_model=SuccessResponse)
@handle_errors
async def get_roles(db: Session = Depends(get_db)):
    """Get all roles"""
    repo = RoleRepository(db)
    roles = repo.get_all_roles()
    role_responses = [RoleResponse.model_validate(role) for role in roles]
    return success_response(
        data=role_responses,
        message="Roles retrieved successfully"
    )

@router.get('/{role_id}', response_model=SuccessResponse)
@handle_errors
async def get_role(role_id: int, db: Session = Depends(get_db)):
    """Get role by ID"""
    repo = RoleRepository(db)
    role = repo.get_role_by_id(role_id)
    validate_entity_exists(role, "Role")
    role_response = RoleResponse.model_validate(role)
    return success_response(
        data=role_response,
        message="Role retrieved successfully"
    )

@router.put('/{role_id}', response_model=SuccessResponse)
@handle_errors
async def update_role(role_id: int, role_data: RoleCreate, db: Session = Depends(get_db)):
    """Update role"""
    repo = RoleRepository(db)
    role = repo.update_role(role_id, role_data.name)
    validate_entity_exists(role, "Role")
    role_response = RoleResponse.model_validate(role)
    return success_response(
        data=role_response,
        message="Role updated successfully"
    )

@router.delete('/{role_id}', response_model=SuccessResponse)
@handle_errors
async def delete_role(role_id: int, db: Session = Depends(get_db)):
    """Delete role"""
    repo = RoleRepository(db)
    if not repo.delete_role(role_id):
        raise not_found_error('Role not found')
    return success_response(
        data=None,
        message="Role deleted successfully"
    )
