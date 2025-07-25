from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..repositories.role_repository import RoleRepository
from pydantic import BaseModel

class RoleCreate(BaseModel):
    name: str

class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

router = APIRouter(prefix='/roles', tags=['Roles'])

@router.post('/', response_model=RoleResponse)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    existing = repo.get_role_by_name(role_data.name)
    if existing:
        raise HTTPException(status_code=400, detail='Role already exists')
    role = repo.create_role(role_data.name)
    return role

@router.get('/', response_model=List[RoleResponse])
def get_roles(db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    return repo.get_all_roles()

@router.get('/{role_id}', response_model=RoleResponse)
def get_role(role_id: int, db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    role = repo.get_role_by_id(role_id)
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    return role

@router.put('/{role_id}', response_model=RoleResponse)
def update_role(role_id: int, role_data: RoleCreate, db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    role = repo.update_role(role_id, role_data.name)
    if not role:
        raise HTTPException(status_code=404, detail='Role not found')
    return role

@router.delete('/{role_id}')
def delete_role(role_id: int, db: Session = Depends(get_db)):
    repo = RoleRepository(db)
    if not repo.delete_role(role_id):
        raise HTTPException(status_code=404, detail='Role not found')
    return {'message': 'Role deleted'} 