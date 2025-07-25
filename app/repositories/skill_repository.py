from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.skill import Skill
from ..models.user_skill import UserSkill
from sqlalchemy import func

class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_skill(self, name: str) -> Skill:
        existing = self.db.query(Skill).filter(func.lower(Skill.name) == func.lower(name)).first()
        if existing:
            return existing
        skill = Skill(name=name)
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def get_skill_by_id(self, skill_id: int) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.id == skill_id, Skill.is_deleted == False).first()

    def get_skills_by_name(self, name: str) -> List[Skill]:
        return self.db.query(Skill).filter(Skill.name.ilike(f"%{name}%"), Skill.is_deleted == False).all()

    def get_all_skills(self) -> List[Skill]:
        return self.db.query(Skill).filter(Skill.is_deleted == False).all()

    def update_skill(self, skill_id: int, name: str) -> Optional[Skill]:
        skill = self.get_skill_by_id(skill_id)
        if skill:
            skill.name = name
            self.db.commit()
            self.db.refresh(skill)
        return skill

    def delete_skill(self, skill_id: int) -> bool:
        skill = self.get_skill_by_id(skill_id)
        if skill:
            skill.is_deleted = True
            self.db.commit()
            return True
        return False

    def add_skill_to_user(self, user_id: int, skill_id: int) -> bool:
        existing = self.db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id).first()
        if existing:
            return False
        user_skill = UserSkill(user_id=user_id, skill_id=skill_id)
        self.db.add(user_skill)
        self.db.commit()
        return True

    def remove_skill_from_user(self, user_id: int, skill_id: int) -> bool:
        user_skill = self.db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id).first()
        if not user_skill:
            return False
        self.db.delete(user_skill)
        self.db.commit()
        return True

    def get_user_skills(self, user_id: int) -> List[Skill]:
        return self.db.query(Skill).join(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.is_deleted == False, Skill.is_deleted == False).all() 