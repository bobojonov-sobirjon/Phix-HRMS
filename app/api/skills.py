from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositories.skill_repository import SkillRepository
from ..schemas.profile import SkillResponse, SkillCreate, SkillUpdate
from ..schemas.common import SuccessResponse
from ..utils.decorators import handle_errors
from ..utils.response_helpers import success_response, not_found_error, validate_entity_exists, forbidden_error
from ..utils.permissions import is_admin_user
from typing import List, Optional
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/skills", tags=["Skills"])

@router.get("/", response_model=SuccessResponse, tags=["Skills"])
@handle_errors
async def get_skills(
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    db: Session = Depends(get_db)
):
    """Get all skills or filter by name"""
    repo = SkillRepository(db)
    if name:
        skills = repo.get_skills_by_name(name)
    else:
        skills = repo.get_all_skills()
    skill_responses = [SkillResponse.model_validate(skill) for skill in skills]
    return success_response(
        data=skill_responses,
        message="Skills retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse, tags=["Skills"])
@handle_errors
async def create_skill(
    skill: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new skill"""
    repo = SkillRepository(db)
    created_skill = repo.create_skill(skill.name)
    skill_response = SkillResponse.model_validate(created_skill)
    return success_response(
        data=skill_response,
        message="Skill created successfully"
    )

@router.patch("/{skill_id}", response_model=SuccessResponse, tags=["Skills"])
@handle_errors
async def update_skill(
    skill_id: int,
    skill: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update skill (admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can update skills")
    repo = SkillRepository(db)
    updated = repo.update_skill(skill_id, skill.name)
    validate_entity_exists(updated, "Skill")
    skill_response = SkillResponse.model_validate(updated)
    return success_response(
        data=skill_response,
        message="Skill updated successfully"
    )

@router.delete("/{skill_id}", response_model=SuccessResponse, tags=["Skills"])
@handle_errors
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete skill (admin only)"""
    if not is_admin_user(current_user.email):
        raise forbidden_error("Only admin can delete skills")
    repo = SkillRepository(db)
    if not repo.delete_skill(skill_id):
        raise not_found_error("Skill not found")
    return success_response(
        data=None,
        message="Skill deleted successfully"
    )
