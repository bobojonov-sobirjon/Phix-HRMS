from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.user_repository import UserRepository
from ..schemas.profile import UserFullResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=UserFullResponse)
def get_user_profile(user_id: int = Header(..., description="User ID to retrieve profile for"), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_user_full_profile(user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return UserFullResponse.from_orm(user)

@router.patch("/", response_model=UserFullResponse)
def update_user_profile(
    user_update: UserUpdate = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    repo = UserRepository(db)
    user = repo.update_user_profile(current_user.id, user_update.dict(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserFullResponse.from_orm(user) 