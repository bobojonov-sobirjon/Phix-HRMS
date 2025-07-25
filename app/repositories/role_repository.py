from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.role import Role

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_role(self, name: str) -> Role:
        role = Role(name=name)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_all_roles(self) -> List[Role]:
        return self.db.query(Role).all()
    
    def update_role(self, role_id: int, name: str) -> Optional[Role]:
        role = self.get_role_by_id(role_id)
        if role:
            role.name = name
            self.db.commit()
            self.db.refresh(role)
        return role
    
    def delete_role(self, role_id: int) -> bool:
        role = self.get_role_by_id(role_id)
        if role:
            self.db.delete(role)
            self.db.commit()
            return True
        return False 

    def seed_initial_roles(self):
        roles = ['user', 'admin']
        for role_name in roles:
            if not self.get_role_by_name(role_name):
                self.create_role(role_name) 