from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import SkillResponse, SkillCreate, SkillUpdate
from typing import List, Optional
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("/", response_model=List[SkillResponse], tags=["Skills"])
def get_skills(
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    db: Session = Depends(get_db)
):
    repo = SkillRepository(db)
    if name:
        return repo.get_skills_by_name(name)
    return repo.get_all_skills()

@router.post("/", response_model=SkillResponse, tags=["Skills"])
def create_skill(skill: SkillCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SkillRepository(db)
    return repo.create_skill(skill.name)

@router.patch("/{skill_id}", response_model=SkillResponse, tags=["Skills"])
def update_skill(skill_id: int, skill: SkillUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SkillRepository(db)
    updated = repo.update_skill(skill_id, skill.name)
    if not updated:
        raise HTTPException(status_code=404, detail="Skill not found")
    return updated

@router.delete("/{skill_id}", tags=["Skills"])
def delete_skill(skill_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SkillRepository(db)
    if not repo.delete_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"message": "Skill deleted successfully"}

@router.get("/user/{user_id}", response_model=List[SkillResponse], tags=["Skills"])
def get_user_skills(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = SkillRepository(db)
    return repo.get_user_skills(user_id) 