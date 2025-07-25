from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.project import Project
from ..models.project_image import ProjectImage
from ..schemas.profile import ProjectCreate

class ProjectRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, user_id: int, project_data: ProjectCreate) -> Project:
        project_dict = project_data.dict(exclude={'images'})
        project = Project(user_id=user_id, **project_dict)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        for img_url in project_data.images:
            image = ProjectImage(project_id=project.id, image=img_url)
            self.db.add(image)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()

    def get_projects_by_user(self, user_id: int) -> List[Project]:
        return self.db.query(Project).filter(Project.user_id == user_id, Project.is_deleted == False).all()

    def update_project(self, project_id: int, update_data: Dict) -> Optional[Project]:
        project = self.get_project_by_id(project_id)
        if not project:
            return None
        for key, value in update_data.items():
            if key != 'images':
                setattr(project, key, value)
        if 'images' in update_data and update_data['images'] is not None:
            self.db.query(ProjectImage).filter(ProjectImage.project_id == project_id).delete()
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
            self.db.commit()
            return True
        return False 