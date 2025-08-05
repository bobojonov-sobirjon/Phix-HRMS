from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import UserSkillResponse, UserSkillCreate, UserSkillCreateWithoutUser, UserSkillCreateBySkillName, SkillResponse
from ..models.user_skill import UserSkill

router = APIRouter(prefix="/user-skills", tags=["Profile Skills"])

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

@router.get("/search", response_model=List[SkillResponse])
def search_skills_by_name(
    name: str = Query(..., description="Skill name to search for"),
    db: Session = Depends(get_db)
):
    """Search skills by name"""
    repo = SkillRepository(db)
    skills = repo.get_skills_by_name(name)
    return skills

@router.post("/", response_model=UserSkillResponse,)
def create_user_skill_by_skill_name(
    data: UserSkillCreateBySkillName, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create user skill by skill name. If skill doesn't exist, create it first."""
    repo = SkillRepository(db)
    
    # First check if skill exists
    existing_skills = repo.get_skills_by_name(data.skill_name)
    
    if existing_skills:
        # Use the first matching skill (case-insensitive match)
        skill = existing_skills[0]
    else:
        # Create new skill if it doesn't exist
        skill = repo.create_skill(data.skill_name)
    
    # Add skill to user
    if not repo.add_skill_to_user(current_user.id, skill.id):
        raise HTTPException(status_code=400, detail="Association already exists")
    
    # Get the created user skill
    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id, 
        UserSkill.skill_id == skill.id
    ).first()
    
    return user_skill

@router.delete("/{user_skill_id}")
def delete_user_skill(user_skill_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id, UserSkill.is_deleted == False).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="UserSkill not found")
    user_skill.is_deleted = True
    db.commit()
    return {"message": "UserSkill deleted successfully"} 