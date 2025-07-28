from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..repositories.user_repository import UserRepository
from ..repositories.skill_repository import SkillRepository
from ..repositories.education_repository import EducationRepository
from ..repositories.experience_repository import ExperienceRepository
from ..repositories.certification_repository import CertificationRepository
from ..repositories.project_repository import ProjectRepository
from ..schemas.profile import (
    UserFullResponse,
    SkillResponse, SkillCreate,
    EducationResponse, EducationCreate, EducationUpdate,
    ExperienceResponse, ExperienceCreate, ExperienceUpdate,
    CertificationResponse, CertificationCreate, CertificationUpdate,
    ProjectResponse, ProjectCreate, ProjectUpdate
)
from typing import List
import os

router = APIRouter(prefix="/profile", tags=[])

# Educations
@router.get("/educations", response_model=List[EducationResponse], tags=["Profile Education"])
def get_my_educations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = EducationRepository(db)
    return repo.get_educations_by_user(current_user.id)

@router.post("/educations", response_model=EducationResponse, tags=["Profile Education"])
def add_education(education: EducationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = EducationRepository(db)
    return repo.create_education(current_user.id, education)

@router.patch("/educations/{education_id}", response_model=EducationResponse, tags=["Profile Education"])
def update_education(education_id: int, education: EducationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = EducationRepository(db)
    updated = repo.update_education(education_id, education.dict(exclude_unset=True))
    if not updated or updated.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Education not found")
    return updated

@router.delete("/educations/{education_id}", tags=["Profile Education"])
def delete_education(education_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = EducationRepository(db)
    if not repo.delete_education(education_id, current_user.id):
        raise HTTPException(status_code=404, detail="Education not found")
    return {"message": "Education deleted"}

# Experiences
@router.get("/experiences", response_model=List[ExperienceResponse], tags=["Profile Experience"])
def get_my_experiences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ExperienceRepository(db)
    return repo.get_experiences_by_user(current_user.id)

@router.post("/experiences", response_model=ExperienceResponse, tags=["Profile Experience"])
def add_experience(data: ExperienceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ExperienceRepository(db)
    return repo.create_experience(current_user.id, data)

@router.patch("/experiences/{id}", response_model=ExperienceResponse, tags=["Profile Experience"])
def update_experience(id: int, data: ExperienceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ExperienceRepository(db)
    updated = repo.update_experience(id, data.dict(exclude_unset=True))
    if not updated or updated.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experience not found")
    return updated

@router.delete("/experiences/{id}", tags=["Profile Experience"])
def delete_experience(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ExperienceRepository(db)
    if not repo.delete_experience(id, current_user.id):
        raise HTTPException(status_code=404, detail="Experience not found")
    return {"message": "Experience deleted"}

# Certifications
@router.get("/certifications", response_model=List[CertificationResponse], tags=["Profile Certifications"])
def get_my_certifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = CertificationRepository(db)
    return repo.get_certifications_by_user(current_user.id)

@router.post("/certifications", response_model=CertificationResponse, tags=["Profile Certifications"])
def add_certification(data: CertificationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = CertificationRepository(db)
    return repo.create_certification(current_user.id, data)

@router.patch("/certifications/{id}", response_model=CertificationResponse, tags=["Profile Certifications"])
def update_certification(id: int, data: CertificationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = CertificationRepository(db)
    updated = repo.update_certification(id, data.dict(exclude_unset=True))
    if not updated or updated.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Certification not found")
    return updated

@router.delete("/certifications/{id}", tags=["Profile Certifications"])
def delete_certification(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = CertificationRepository(db)
    if not repo.delete_certification(id, current_user.id):
        raise HTTPException(status_code=404, detail="Certification not found")
    return {"message": "Certification deleted"}

# Projects
@router.get("/projects", response_model=List[ProjectResponse], tags=["Profile Projects"])
def get_my_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    return repo.get_projects_by_user(current_user.id)

@router.post("/projects", response_model=ProjectResponse, tags=["Profile Projects"])
async def add_project(
    project_name: str = Form(...),
    role: str = Form(None),
    from_date: str = Form(None),
    to_date: str = Form(None),
    live_project_path: str = Form(None),
    description: str = Form(None),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    from datetime import datetime
    import os
    from ..models.project import Project
    from ..models.project_image import ProjectImage

    # Parse dates
    from_date_parsed = datetime.fromisoformat(from_date) if from_date else None
    to_date_parsed = datetime.fromisoformat(to_date) if to_date else None

    # Create project
    project = Project(
        user_id=current_user.id,
        project_name=project_name,
        role=role,
        from_date=from_date_parsed,
        to_date=to_date_parsed,
        live_project_path=live_project_path,
        description=description
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Handle images
    image_objs = []
    if images:
        upload_dir = "static/projects"
        os.makedirs(upload_dir, exist_ok=True)
        for img in images:
            if img.content_type.startswith('image/'):
                filename = f"{project.id}_{img.filename}"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as buffer:
                    buffer.write(await img.read())
                rel_path = f"/{file_path.replace('\\', '/')}"
                image_obj = ProjectImage(project_id=project.id, image=rel_path)
                db.add(image_obj)
                image_objs.append(image_obj)
        db.commit()

    db.refresh(project)
    # Attach images to project for response
    project.images = image_objs if image_objs else []

    # Add base URL to image paths in response
    base_url = str(request.base_url).rstrip("/")
    for img in project.images:
        if img.image and not img.image.startswith("http"):
            img.image = f"{base_url}{img.image}"

    return project

@router.patch("/projects/{id}", response_model=ProjectResponse, tags=["Profile Projects"])
def update_project(id: int, data: ProjectUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    updated = repo.update_project(id, data.dict(exclude_unset=True))
    if not updated or updated.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated

@router.delete("/projects/{id}", tags=["Profile Projects"])
def delete_project(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = ProjectRepository(db)
    if not repo.delete_project(id, current_user.id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}

@router.post("/avatar", response_model=UserFullResponse, tags=["User Profile"])
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only images allowed")
    upload_dir = "static/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    current_user.avatar_url = f"/{file_path}"
    db.commit()
    db.refresh(current_user)
    return UserFullResponse.model_validate(current_user) 