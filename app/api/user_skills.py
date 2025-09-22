from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import UserSkillResponse, UserSkillCreate, UserSkillCreateWithoutUser, UserSkillCreateBySkillName, UserSkillCreateBySkillId, SkillResponse, UserSkillWithDetailsResponse
from ..schemas.common import SuccessResponse
from ..models.user_skill import UserSkill

router = APIRouter(prefix="/user-skills", tags=["Profile Skills"])

@router.get("/", response_model=SuccessResponse)
def get_user_skills(
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from ..models.skill import Skill
        
        # Join UserSkill with Skill to get skill details
        query = db.query(UserSkill, Skill).join(Skill, UserSkill.skill_id == Skill.id).filter(
            UserSkill.is_deleted == False,
            Skill.is_deleted == False,
            UserSkill.user_id == current_user.id
        )
        
        if skill_id:
            query = query.filter(UserSkill.skill_id == skill_id)
            
        results = query.all()
        
        # Convert to response models with skill details
        user_skill_responses = []
        for user_skill, skill in results:
            skill_response = SkillResponse.model_validate(skill)
            user_skill_response = UserSkillWithDetailsResponse(
                id=user_skill.id,
                skill_details=skill_response,
                created_at=user_skill.created_at,
                updated_at=user_skill.updated_at
            )
            user_skill_responses.append(user_skill_response)
            
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
def create_user_skill_by_skill_id(
    data: UserSkillCreateBySkillId, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Create multiple user skills by skill IDs."""
    try:
        from ..models.skill import Skill
        created_user_skills = []
        existing_skills = []
        not_found_skills = []
        
        for skill_id in data.skill_ids:
            # Check if skill exists
            skill = db.query(Skill).filter(
                Skill.id == skill_id,
                Skill.is_deleted == False
            ).first()
            
            if not skill:
                not_found_skills.append(skill_id)
                continue
            
            # Check if user already has this skill (only non-deleted ones)
            existing_user_skill = db.query(UserSkill).filter(
                UserSkill.user_id == current_user.id,
                UserSkill.skill_id == skill_id,
                UserSkill.is_deleted == False
            ).first()
            
            if existing_user_skill:
                existing_skills.append(skill.name)
                continue
            
            # Add skill to user
            user_skill = UserSkill(
                user_id=current_user.id,
                skill_id=skill_id
            )
            db.add(user_skill)
            db.flush()  # Flush to get the ID
            
            # Convert SQLAlchemy model to Pydantic response model
            user_skill_response = UserSkillResponse.model_validate(user_skill)
            created_user_skills.append(user_skill_response)
        
        db.commit()
        
        # Prepare response message
        message_parts = []
        
        if created_user_skills:
            message_parts.append(f"Successfully added {len(created_user_skills)} new skills")
        
        if existing_skills:
            existing_skills_str = ", ".join(existing_skills)
            message_parts.append(f"Already have these skills: {existing_skills_str}")
        
        if not_found_skills:
            not_found_str = ", ".join(map(str, not_found_skills))
            message_parts.append(f"Skills not found: {not_found_str}")
        
        if not created_user_skills and not existing_skills and not not_found_skills:
            raise HTTPException(status_code=400, detail="No valid skills provided")
        
        if not created_user_skills and existing_skills:
            # All skills already exist
            existing_skills_str = ", ".join(existing_skills)
            raise HTTPException(status_code=400, detail=f"All skills already exist: {existing_skills_str}. Please add different skills.")
        
        if not created_user_skills and not_found_skills:
            # All skills not found
            not_found_str = ", ".join(map(str, not_found_skills))
            raise HTTPException(status_code=400, detail=f"Skills not found: {not_found_str}")
        
        return SuccessResponse(
            msg="; ".join(message_parts)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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

@router.post("/cleanup-duplicates", response_model=SuccessResponse)
def cleanup_duplicate_skills(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove duplicate skills for the current user"""
    try:
        # Find all user skills for current user
        user_skills = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.is_deleted == False
        ).all()
        
        # Group by skill_id and keep only the first one
        skill_groups = {}
        duplicates_removed = 0
        
        for user_skill in user_skills:
            skill_id = user_skill.skill_id
            if skill_id not in skill_groups:
                skill_groups[skill_id] = user_skill
            else:
                # Mark as duplicate and soft delete
                user_skill.is_deleted = True
                duplicates_removed += 1
        
        db.commit()
        
        return SuccessResponse(
            msg=f"Successfully removed {duplicates_removed} duplicate skills"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 