from sqlalchemy.orm import Session, selectinload
from typing import List, Optional, Dict
from ..models.project import Project
from ..models.project_image import ProjectImage
from ..schemas.profile import ProjectCreate

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, user_id: int, project_data) -> Project:
        try:
            if hasattr(project_data, 'dict'):
                project_dict = project_data.dict(exclude={'images'})
            elif hasattr(project_data, 'model_dump'):
                project_dict = project_data.model_dump(exclude={'images'})
            else:
                project_dict = project_data.copy()
            
            project_dict = {k: v for k, v in project_dict.items() if v is not None}
            
            project = Project(user_id=user_id, **project_dict)
            self.db.add(project)
            self.db.flush()
            
            if hasattr(project_data, 'images') and project_data.images:
                for img_url in project_data.images:
                    if img_url:
                        image = ProjectImage(project_id=project.id, image=img_url)
                        self.db.add(image)
            
            self.db.commit()
            self.db.refresh(project)
            return project
        except Exception as e:
            self.db.rollback()
            from ..core.logging_config import logger
            logger.error(f"Error creating project: {e}", exc_info=True)
            raise

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).options(
            selectinload(Project.images)
        ).filter(Project.id == project_id, Project.is_deleted == False).first()

    def get_projects_by_user(self, user_id: int) -> List[Project]:
        return self.db.query(Project).options(
            selectinload(Project.images)
        ).filter(Project.user_id == user_id, Project.is_deleted == False).all()

    def update_project(self, project_id: int, update_data: Dict) -> Optional[Project]:
        project = self.get_project_by_id(project_id)
        if not project:
            return None
            
        for key, value in update_data.items():
            if key != 'images' and hasattr(project, key):
                setattr(project, key, value)
        
        if 'images' in update_data and update_data['images'] is not None:
            self.db.query(ProjectImage).filter(
                ProjectImage.project_id == project_id,
                ProjectImage.is_deleted == False
            ).update({"is_deleted": True})
            
            for img_url in update_data['images']:
                image = ProjectImage(project_id=project_id, image=img_url)
                self.db.add(image)
        
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int, user_id: int) -> bool:
        project = self.get_project_by_id(project_id)
        if project and project.user_id == user_id:
            project.is_deleted = True
            for image in project.images:
                image.is_deleted = True
            self.db.commit()
            return True
        return False 