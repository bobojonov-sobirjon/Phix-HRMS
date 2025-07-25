from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import UserSkillResponse, UserSkillCreate, UserSkillCreateWithoutUser
from ..models.user_skill import UserSkill

router = APIRouter(prefix="/user-skills", tags=["User Skills"])

@router.get("/", response_model=List[UserSkillResponse])
def get_user_skills(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(UserSkill).filter(UserSkill.is_deleted == False)
    if user_id:
        query = query.filter(UserSkill.user_id == user_id)
    if skill_id:
        query = query.filter(UserSkill.skill_id == skill_id)
    return query.all()

@router.post("/", response_model=UserSkillResponse)
def create_user_skill(data: UserSkillCreateWithoutUser, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SkillRepository(db)
    if not repo.add_skill_to_user(current_user.id, data.skill_id):
        raise HTTPException(status_code=400, detail="Association already exists or invalid IDs")
    user_skill = db.query(UserSkill).filter(UserSkill.user_id == current_user.id, UserSkill.skill_id == data.skill_id).first()
    return user_skill

@router.delete("/{user_skill_id}")
def delete_user_skill(user_skill_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id, UserSkill.is_deleted == False).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="UserSkill not found")
    user_skill.is_deleted = True
    db.commit()
    return {"message": "UserSkill deleted successfully"} 