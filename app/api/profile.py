from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..models.language import Language
from ..utils.auth import get_current_user
from ..repositories.user_repository import UserRepository
from ..repositories.skill_repository import SkillRepository
from ..repositories.education_repository import EducationRepository
from ..repositories.experience_repository import ExperienceRepository
from ..repositories.certification_repository import CertificationRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.language_repository import LanguageRepository
from ..schemas.profile import (
    UserFullResponse,
    SkillResponse, SkillCreate,
    EducationResponse, EducationCreate, EducationUpdate,
    ExperienceResponse, ExperienceCreate, ExperienceUpdate,
    CertificationResponse, CertificationCreate, CertificationUpdate,
    ProjectResponse, ProjectCreate, ProjectUpdate,
    UserLanguageUpdate
)
from ..schemas.common import SuccessResponse, ErrorResponse
from typing import List
import os

router = APIRouter(prefix="/profile", tags=[])

# Educations
@router.get("/educations", response_model=SuccessResponse, tags=["Profile Education"])
def get_my_educations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = EducationRepository(db)
        educations = repo.get_educations_by_user(current_user.id)
        # Convert SQLAlchemy models to Pydantic response models
        education_responses = [EducationResponse.model_validate(edu) for edu in educations]
        return SuccessResponse(
            msg="Educations retrieved successfully",
            data=education_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
def get_education_by_id(education_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = EducationRepository(db)
        education = repo.get_education_by_id(education_id)
        if not education or education.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Education not found")
        # Convert SQLAlchemy model to Pydantic response model
        education_response = EducationResponse.model_validate(education)
        return SuccessResponse(
            msg="Education retrieved successfully",
            data=education_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/educations", response_model=SuccessResponse, tags=["Profile Education"])
def add_education(education: EducationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = EducationRepository(db)
        created_education = repo.create_education(current_user.id, education)
        # Convert SQLAlchemy model to Pydantic response model
        education_response = EducationResponse.model_validate(created_education)
        return SuccessResponse(
            msg="Education added successfully",
            data=education_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
def update_education(education_id: int, education: EducationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = EducationRepository(db)
        updated = repo.update_education(education_id, education.dict(exclude_unset=True))
        if not updated or updated.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Education not found")
        # Convert SQLAlchemy model to Pydantic response model
        education_response = EducationResponse.model_validate(updated)
        return SuccessResponse(
            msg="Education updated successfully",
            data=education_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
def delete_education(education_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = EducationRepository(db)
        if not repo.delete_education(education_id, current_user.id):
            raise HTTPException(status_code=404, detail="Education not found")
        return SuccessResponse(msg="Education deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Experiences
@router.get("/experiences", response_model=SuccessResponse, tags=["Profile Experience"])
def get_my_experiences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ExperienceRepository(db)
        experiences = repo.get_experiences_by_user(current_user.id)
        # Convert SQLAlchemy models to Pydantic response models
        experience_responses = [ExperienceResponse.model_validate(exp) for exp in experiences]
        return SuccessResponse(
            msg="Experiences retrieved successfully",
            data=experience_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
def get_experience_by_id(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ExperienceRepository(db)
        experience = repo.get_experience_by_id(id)
        if not experience or experience.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Experience not found")
        # Convert SQLAlchemy model to Pydantic response model
        experience_response = ExperienceResponse.model_validate(experience)
        return SuccessResponse(
            msg="Experience retrieved successfully",
            data=experience_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/experiences", response_model=SuccessResponse, tags=["Profile Experience"])
def add_experience(data: ExperienceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ExperienceRepository(db)
        created_experience = repo.create_experience(current_user.id, data)
        # Convert SQLAlchemy model to Pydantic response model
        experience_response = ExperienceResponse.model_validate(created_experience)
        return SuccessResponse(
            msg="Experience added successfully",
            data=experience_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
def update_experience(id: int, data: ExperienceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ExperienceRepository(db)
        updated = repo.update_experience(id, data.dict(exclude_unset=True))
        if not updated or updated.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Experience not found")
        # Convert SQLAlchemy model to Pydantic response model
        experience_response = ExperienceResponse.model_validate(updated)
        return SuccessResponse(
            msg="Experience updated successfully",
            data=experience_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
def delete_experience(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ExperienceRepository(db)
        if not repo.delete_experience(id, current_user.id):
            raise HTTPException(status_code=404, detail="Experience not found")
        return SuccessResponse(msg="Experience deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Certifications
@router.get("/certifications", response_model=SuccessResponse, tags=["Profile Certifications"])
def get_my_certifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = CertificationRepository(db)
        certifications = repo.get_certifications_by_user(current_user.id)
        # Convert SQLAlchemy models to Pydantic response models
        certification_responses = [CertificationResponse.model_validate(cert) for cert in certifications]
        return SuccessResponse(
            msg="Certifications retrieved successfully",
            data=certification_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
def get_certification_by_id(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = CertificationRepository(db)
        certification = repo.get_certification_by_id(id)
        if not certification or certification.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Certification not found")
        # Convert SQLAlchemy model to Pydantic response model
        certification_response = CertificationResponse.model_validate(certification)
        return SuccessResponse(
            msg="Certification retrieved successfully",
            data=certification_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/certifications", response_model=SuccessResponse, tags=["Profile Certifications"])
def add_certification(data: CertificationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = CertificationRepository(db)
        created_certification = repo.create_certification(current_user.id, data)
        # Convert SQLAlchemy model to Pydantic response model
        certification_response = CertificationResponse.model_validate(created_certification)
        return SuccessResponse(
            msg="Certification added successfully",
            data=certification_response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
def update_certification(id: int, data: CertificationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = CertificationRepository(db)
        updated = repo.update_certification(id, data.dict(exclude_unset=True))
        if not updated or updated.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Certification not found")
        # Convert SQLAlchemy model to Pydantic response model
        certification_response = CertificationResponse.model_validate(updated)
        return SuccessResponse(
            msg="Certification updated successfully",
            data=certification_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
def delete_certification(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = CertificationRepository(db)
        if not repo.delete_certification(id, current_user.id):
            raise HTTPException(status_code=404, detail="Certification not found")
        return SuccessResponse(msg="Certification deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Projects
@router.get("/projects", response_model=SuccessResponse, tags=["Profile Projects"])
def get_my_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request = None):
    try:
        repo = ProjectRepository(db)
        projects = repo.get_projects_by_user(current_user.id)
        # Convert SQLAlchemy models to Pydantic response models
        project_responses = [ProjectResponse.model_validate(proj) for proj in projects]
        
        # Add base URL to image paths in response
        base_url = str(request.base_url).rstrip("/") if request else ""
        for project_response in project_responses:
            for img in project_response.images:
                if img.image and not img.image.startswith("http"):
                    img.image = f"{base_url}{img.image}"
        
        return SuccessResponse(
            msg="Projects retrieved successfully",
            data=project_responses
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
def get_project_by_id(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), request: Request = None):
    try:
        repo = ProjectRepository(db)
        project = repo.get_project_by_id(id)
        if not project or project.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Project not found")
        # Convert SQLAlchemy model to Pydantic response model
        project_response = ProjectResponse.model_validate(project)
        
        # Add base URL to image paths in response
        base_url = str(request.base_url).rstrip("/") if request else ""
        for img in project_response.images:
            if img.image and not img.image.startswith("http"):
                img.image = f"{base_url}{img.image}"
        
        return SuccessResponse(
            msg="Project retrieved successfully",
            data=project_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects", response_model=SuccessResponse, tags=["Profile Projects"])
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
    try:
        from datetime import datetime
        import os
        from ..models.project_image import ProjectImage

        # Parse dates
        from_date_parsed = datetime.fromisoformat(from_date) if from_date else None
        to_date_parsed = datetime.fromisoformat(to_date) if to_date else None

        # Prepare project data
        project_data = {
            "project_name": project_name,
            "role": role,
            "from_date": from_date_parsed,
            "to_date": to_date_parsed,
            "live_project_path": live_project_path,
            "description": description
        }

        # Use repository to create project
        repo = ProjectRepository(db)
        project = repo.create_project(current_user.id, project_data)

        # Handle image uploads if provided
        if images:
            upload_dir = "static/projects"
            os.makedirs(upload_dir, exist_ok=True)
            
            for img in images:
                if img.content_type.startswith('image/'):
                    filename = f"{project.id}_{img.filename}"
                    file_path = os.path.join(upload_dir, filename)
                    with open(file_path, "wb") as buffer:
                        buffer.write(await img.read())
                    normalized_path = file_path.replace('\\', '/')
                    rel_path = f"/{normalized_path}"
                    
                    # Create image object
                    image_obj = ProjectImage(project_id=project.id, image=rel_path)
                    db.add(image_obj)
            
            db.commit()
            db.refresh(project)

        # Convert to response model
        project_response = ProjectResponse.model_validate(project)
        
        # Add base URL to image paths in response
        base_url = str(request.base_url).rstrip("/")
        for img in project_response.images:
            if img.image and not img.image.startswith("http"):
                img.image = f"{base_url}{img.image}"

        return SuccessResponse(
            msg="Project added successfully",
            data=project_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
async def update_project(
    id: int, 
    project_name: str = Form(None),
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
    try:
        from datetime import datetime
        import os
        from ..models.project_image import ProjectImage
        
        repo = ProjectRepository(db)
        
        # Check if project exists and belongs to user
        project = repo.get_project_by_id(id)
        if not project or project.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Prepare update data
        update_data = {}
        if project_name is not None:
            update_data['project_name'] = project_name
        if role is not None:
            update_data['role'] = role
        if from_date is not None:
            update_data['from_date'] = datetime.fromisoformat(from_date)
        if to_date is not None:
            update_data['to_date'] = datetime.fromisoformat(to_date)
        if live_project_path is not None:
            update_data['live_project_path'] = live_project_path
        if description is not None:
            update_data['description'] = description
        
        # Handle image updates if provided
        if images:
            image_urls = []
            upload_dir = "static/projects"
            os.makedirs(upload_dir, exist_ok=True)
            
            for img in images:
                if img.content_type.startswith('image/'):
                    filename = f"{project.id}_{img.filename}"
                    file_path = os.path.join(upload_dir, filename)
                    with open(file_path, "wb") as buffer:
                        buffer.write(await img.read())
                    normalized_path = file_path.replace('\\', '/')
                    rel_path = f"/{normalized_path}"
                    image_urls.append(rel_path)
            
            if image_urls:
                update_data['images'] = image_urls
        
        # Update project
        updated = repo.update_project(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Convert SQLAlchemy model to Pydantic response model
        project_response = ProjectResponse.model_validate(updated)
        
        # Add base URL to image paths in response
        base_url = str(request.base_url).rstrip("/")
        for img in project_response.images:
            if img.image and not img.image.startswith("http"):
                img.image = f"{base_url}{img.image}"
        
        return SuccessResponse(
            msg="Project updated successfully",
            data=project_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
def delete_project(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = ProjectRepository(db)
        if not repo.delete_project(id, current_user.id):
            raise HTTPException(status_code=404, detail="Project not found")
        return SuccessResponse(msg="Project deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/avatar", response_model=SuccessResponse, tags=["Profile Avatar Upload and Update"])
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
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
        user_response = UserFullResponse.model_validate(current_user)
        return SuccessResponse(
            msg="Avatar uploaded successfully",
            data=user_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/language", response_model=SuccessResponse, tags=["Profile Language"])
def update_user_language(data: UserLanguageUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Check if language exists
        language_repo = LanguageRepository(db)
        language = language_repo.get(data.language_id)

        if not language:
            raise HTTPException(status_code=404, detail="Language not found")

        # Update user's language
        current_user.language_id = data.language_id
        db.commit()
        db.refresh(current_user)

        user_response = UserFullResponse.model_validate(current_user)
        return SuccessResponse(
            msg="Language updated successfully",
            data=user_response
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 