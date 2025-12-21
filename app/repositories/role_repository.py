from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.role import Role
from .base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """Repository for Role model"""
    
    def __init__(self, db: Session):
        super().__init__(db, Role)
    
    def create_role(self, name: str) -> Role:
        """Create a new role"""
        return self.create({"name": name})
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role by name"""
        roles = self.search("name", name, case_sensitive=True)
        return roles[0] if roles else None
    
    def get_role_by_id(self, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        return self.get_by_id(role_id, include_deleted=False)
    
    def get_all_roles(self) -> List[Role]:
        """Get all roles"""
        return self.get_all(include_deleted=False)
    
    def update_role(self, role_id: int, name: str) -> Optional[Role]:
        """Update role"""
        return self.update(role_id, {"name": name}, exclude_unset=False)
    
    def delete_role(self, role_id: int) -> bool:
        """Hard delete role (roles don't have is_deleted)"""
        return self.delete(role_id, hard_delete=True)
    
    def seed_initial_roles(self):
        """Seed initial roles"""
        roles = ['user', 'admin']
        for role_name in roles:
            if not self.get_role_by_name(role_name):
                self.create_role(role_name)
