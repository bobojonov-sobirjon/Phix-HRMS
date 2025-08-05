from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import SkillResponse, SkillCreate, SkillUpdate
from ..schemas.common import SuccessResponse
from typing import List, Optional
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("/", response_model=SuccessResponse, tags=["Skills"])
def get_skills(
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    db: Session = Depends(get_db)
):
    try:
        repo = SkillRepository(db)
        if name:
            skills = repo.get_skills_by_name(name)
        else:
            skills = repo.get_all_skills()
        # Convert SQLAlchemy models to Pydantic response models
        skill_responses = [SkillResponse.model_validate(skill) for skill in skills]
        return SuccessResponse(
            msg="Skills retrieved successfully",
            data=skill_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse, tags=["Skills"])
def create_skill(skill: SkillCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = SkillRepository(db)
        created_skill = repo.create_skill(skill.name)
        # Convert SQLAlchemy model to Pydantic response model
        skill_response = SkillResponse.model_validate(created_skill)
        return SuccessResponse(
            msg="Skill created successfully",
            data=skill_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{skill_id}", response_model=SuccessResponse, tags=["Skills"])
def update_skill(skill_id: int, skill: SkillUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = SkillRepository(db)
        updated = repo.update_skill(skill_id, skill.name)
        if not updated:
            raise HTTPException(status_code=404, detail="Skill not found")
        # Convert SQLAlchemy model to Pydantic response model
        skill_response = SkillResponse.model_validate(updated)
        return SuccessResponse(
            msg="Skill updated successfully",
            data=skill_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{skill_id}", response_model=SuccessResponse, tags=["Skills"])
def delete_skill(skill_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = SkillRepository(db)
        if not repo.delete_skill(skill_id):
            raise HTTPException(status_code=404, detail="Skill not found")
        return SuccessResponse(msg="Skill deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=SuccessResponse, tags=["Skills"])
def get_user_skills(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = SkillRepository(db)
        skills = repo.get_user_skills(user_id)
        # Convert SQLAlchemy models to Pydantic response models
        skill_responses = [SkillResponse.model_validate(skill) for skill in skills]
        return SuccessResponse(
            msg="User skills retrieved successfully",
            data=skill_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 