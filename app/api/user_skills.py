from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import UserSkillResponse, UserSkillCreate, UserSkillCreateWithoutUser, UserSkillCreateBySkillName, SkillResponse
from ..schemas.common import SuccessResponse
from ..models.user_skill import UserSkill

router = APIRouter(prefix="/user-skills", tags=["Profile Skills"])

@router.get("/", response_model=SuccessResponse)
def get_user_skills(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(UserSkill).filter(UserSkill.is_deleted == False)
        if user_id:
            query = query.filter(UserSkill.user_id == user_id)
        if skill_id:
            query = query.filter(UserSkill.skill_id == skill_id)
        user_skills = query.all()
        # Convert SQLAlchemy models to Pydantic response models
        user_skill_responses = [UserSkillResponse.model_validate(us) for us in user_skills]
        return SuccessResponse(
            msg="User skills retrieved successfully",
            data=user_skill_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SuccessResponse)
def search_skills_by_name(
    name: str = Query(..., description="Skill name to search for"),
    db: Session = Depends(get_db)
):
    """Search skills by name"""
    try:
        repo = SkillRepository(db)
        skills = repo.get_skills_by_name(name)
        # Convert SQLAlchemy models to Pydantic response models
        skill_responses = [SkillResponse.model_validate(skill) for skill in skills]
        return SuccessResponse(
            msg="Skills search completed successfully",
            data=skill_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse)
def create_user_skill_by_skill_name(
    data: UserSkillCreateBySkillName, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create multiple user skills by skill names. If skill doesn't exist, create it first."""
    try:
        repo = SkillRepository(db)
        created_user_skills = []
        
        for skill_name in data.skill_names:
            # First check if skill exists
            existing_skills = repo.get_skills_by_name(skill_name)
            
            if existing_skills:
                # Use the first matching skill (case-insensitive match)
                skill = existing_skills[0]
            else:
                # Create new skill if it doesn't exist
                skill = repo.create_skill(skill_name)
            
            # Add skill to user
            if repo.add_skill_to_user(current_user.id, skill.id):
                # Get the created user skill
                user_skill = db.query(UserSkill).filter(
                    UserSkill.user_id == current_user.id, 
                    UserSkill.skill_id == skill.id
                ).first()
                
                if user_skill:
                    # Convert SQLAlchemy model to Pydantic response model
                    user_skill_response = UserSkillResponse.model_validate(user_skill)
                    created_user_skills.append(user_skill_response)
        
        if not created_user_skills:
            raise HTTPException(status_code=400, detail="No new skills were added")
        
        return SuccessResponse(
            msg=f"Successfully added {len(created_user_skills)} skills to user",
            data=created_user_skills
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/", response_model=SuccessResponse)
def update_user_skills(
    data: UserSkillCreateBySkillName, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Replace all user skills with new ones (delete old, add new)"""
    try:
        repo = SkillRepository(db)
        
        # Delete all existing user skills (soft delete)
        existing_user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.is_deleted == False
        ).all()
        
        for user_skill in existing_user_skills:
            user_skill.is_deleted = True
        
        # Add new skills
        created_user_skills = []
        for skill_name in data.skill_names:
            # First check if skill exists
            existing_skills = repo.get_skills_by_name(skill_name)
            
            if existing_skills:
                # Use the first matching skill (case-insensitive match)
                skill = existing_skills[0]
            else:
                # Create new skill if it doesn't exist
                skill = repo.create_skill(skill_name)
            
            # Add skill to user
            if repo.add_skill_to_user(current_user.id, skill.id):
                # Get the created user skill
                user_skill = db.query(UserSkill).filter(
                    UserSkill.user_id == current_user.id, 
                    UserSkill.skill_id == skill.id
                ).first()
                
                if user_skill:
                    # Convert SQLAlchemy model to Pydantic response model
                    user_skill_response = UserSkillResponse.model_validate(user_skill)
                    created_user_skills.append(user_skill_response)
        
        db.commit()
        
        if not created_user_skills:
            raise HTTPException(status_code=400, detail="No new skills were added")
        
        return SuccessResponse(
            msg=f"Successfully updated user skills. Removed {len(existing_user_skills)} old skills, added {len(created_user_skills)} new skills",
            data=created_user_skills
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_skill_id}", response_model=SuccessResponse)
def delete_user_skill(user_skill_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        user_skill = db.query(UserSkill).filter(UserSkill.id == user_skill_id, UserSkill.is_deleted == False).first()
        if not user_skill:
            raise HTTPException(status_code=404, detail="UserSkill not found")
        user_skill.is_deleted = True
        db.commit()
        return SuccessResponse(msg="UserSkill deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 