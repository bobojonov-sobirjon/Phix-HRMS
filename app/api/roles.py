from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..repositories.role_repository import RoleRepository
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
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    try:
        repo = RoleRepository(db)
        existing = repo.get_role_by_name(role_data.name)
        if existing:
            raise HTTPException(status_code=400, detail='Role already exists')
        role = repo.create_role(role_data.name)
        # Convert SQLAlchemy model to Pydantic response model
        role_response = RoleResponse.model_validate(role)
        return SuccessResponse(
            msg="Role created successfully",
            data=role_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/', response_model=SuccessResponse)
def get_roles(db: Session = Depends(get_db)):
    try:
        repo = RoleRepository(db)
        roles = repo.get_all_roles()
        # Convert SQLAlchemy models to Pydantic response models
        role_responses = [RoleResponse.model_validate(role) for role in roles]
        return SuccessResponse(
            msg="Roles retrieved successfully",
            data=role_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/{role_id}', response_model=SuccessResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    try:
        repo = RoleRepository(db)
        role = repo.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail='Role not found')
        # Convert SQLAlchemy model to Pydantic response model
        role_response = RoleResponse.model_validate(role)
        return SuccessResponse(
            msg="Role retrieved successfully",
            data=role_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/{role_id}', response_model=SuccessResponse)
def update_role(role_id: int, role_data: RoleCreate, db: Session = Depends(get_db)):
    try:
        repo = RoleRepository(db)
        role = repo.update_role(role_id, role_data.name)
        if not role:
            raise HTTPException(status_code=404, detail='Role not found')
        # Convert SQLAlchemy model to Pydantic response model
        role_response = RoleResponse.model_validate(role)
        return SuccessResponse(
            msg="Role updated successfully",
            data=role_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/{role_id}', response_model=SuccessResponse)
def delete_role(role_id: int, db: Session = Depends(get_db)):
    try:
        repo = RoleRepository(db)
        if not repo.delete_role(role_id):
            raise HTTPException(status_code=404, detail='Role not found')
        return SuccessResponse(msg="Role deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 