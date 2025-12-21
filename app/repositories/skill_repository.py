from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.skill import Skill
from ..models.user_skill import UserSkill
from sqlalchemy import func
from .base_repository import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    """Repository for Skill model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Skill)
    
    def create_skill(self, name: str) -> Skill:
        """Create a new skill or return existing one"""
        existing = self.db.query(Skill).filter(
            func.lower(Skill.name) == func.lower(name),
            Skill.is_deleted == False
        ).first()
        if existing:
            return existing
        return self.create({"name": name})
    
    def get_skill_by_id(self, skill_id: int) -> Optional[Skill]:
        """Get skill by ID (excluding deleted)"""
        return self.get_by_id(skill_id, include_deleted=False)
    
    def get_skills_by_name(self, name: str) -> List[Skill]:
        """Get skills by name (partial match, case-insensitive)"""
        return self.search("name", name, case_sensitive=False)
    
    def get_all_skills(self) -> List[Skill]:
        """Get all skills (excluding deleted)"""
        return self.get_all(include_deleted=False)
    
    def update_skill(self, skill_id: int, name: str) -> Optional[Skill]:
        """Update skill name"""
        return self.update(skill_id, {"name": name}, exclude_unset=False)
    
    def delete_skill(self, skill_id: int) -> bool:
        """Soft delete skill"""
        return self.delete(skill_id, hard_delete=False)
    
    def add_skill_to_user(self, user_id: int, skill_id: int) -> bool:
        """Add skill to user"""
        existing = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
            UserSkill.is_deleted == False
        ).first()
        if existing:
            return False
        user_skill = UserSkill(user_id=user_id, skill_id=skill_id)
        self.db.add(user_skill)
        self.db.commit()
        return True
    
    def remove_skill_from_user(self, user_id: int, skill_id: int) -> bool:
        """Remove skill from user"""
        user_skill = self.db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill_id,
            UserSkill.is_deleted == False
        ).first()
        if not user_skill:
            return False
        if hasattr(user_skill, 'is_deleted'):
            user_skill.is_deleted = True
        else:
            self.db.delete(user_skill)
        self.db.commit()
        return True
    
    def get_user_skills(self, user_id: int) -> List[Skill]:
        """Get all skills for a user"""
        return self.db.query(Skill).join(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.is_deleted == False,
            Skill.is_deleted == False
        ).all() 