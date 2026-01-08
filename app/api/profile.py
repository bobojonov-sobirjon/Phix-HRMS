from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from typing import List, Optional
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..models.user import User
from ..models.language import Language
from ..utils.auth import get_current_user
from ..utils.decorators import handle_errors
from ..utils.response_helpers import (
    success_response,
    not_found_error,
    bad_request_error,
    validate_entity_exists,
    validate_ownership
)
from ..repositories.user_repository import UserRepository
from ..repositories.skill_repository import SkillRepository
from ..repositories.education_repository import EducationRepository
from ..repositories.experience_repository import ExperienceRepository
from ..repositories.certification_repository import CertificationRepository
from ..repositories.project_repository import ProjectRepository
from ..repositories.language_repository import LanguageRepository
from ..repositories.category_repository import CategoryRepository
from ..schemas.profile import (
    UserFullResponse,
    SkillResponse, SkillCreate,
    EducationResponse, EducationCreate, EducationUpdate,
    ExperienceResponse, ExperienceCreate, ExperienceUpdate,
    CertificationResponse, CertificationCreate, CertificationUpdate,
    ProjectResponse, ProjectCreate, ProjectUpdate,
    UserLanguageUpdate
)
from ..schemas.category import CategoryResponse
from ..schemas.common import SuccessResponse, ErrorResponse
import os

router = APIRouter(prefix="/profile", tags=[])

@router.get("/user/{user_id}", response_model=SuccessResponse, tags=["Account"])
@handle_errors
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """
    Get user profile by ID (public endpoint)
    
    - **user_id**: ID of the user to retrieve
    """
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    validate_entity_exists(user, "User")
    
    user_response = UserFullResponse.model_validate(user)
    return success_response(
        data=user_response,
        message="User retrieved successfully"
    )

@router.get("/educations", response_model=SuccessResponse, tags=["Profile Education"])
@handle_errors
async def get_my_educations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all educations for current user"""
    repo = EducationRepository(db)
    educations = repo.get_educations_by_user(current_user.id)
    education_responses = [EducationResponse.model_validate(edu) for edu in educations]
    return success_response(
        data=education_responses,
        message="Educations retrieved successfully"
    )

@router.get("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
@handle_errors
async def get_education_by_id(education_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get education by ID"""
    repo = EducationRepository(db)
    education = repo.get_education_by_id(education_id)
    validate_entity_exists(education, "Education")
    validate_ownership(education.user_id, current_user.id, "Education")
    education_response = EducationResponse.model_validate(education)
    return success_response(
        data=education_response,
        message="Education retrieved successfully"
    )

@router.post("/educations", response_model=SuccessResponse, tags=["Profile Education"])
@handle_errors
async def add_education(education: EducationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add new education"""
    repo = EducationRepository(db)
    created_education = repo.create_education(current_user.id, education)
    education_response = EducationResponse.model_validate(created_education)
    return success_response(
        data=education_response,
        message="Education added successfully"
    )

@router.patch("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
@handle_errors
async def update_education(education_id: int, education: EducationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update education"""
    repo = EducationRepository(db)
    updated = repo.update_education(education_id, education.dict(exclude_unset=True))
    validate_entity_exists(updated, "Education")
    validate_ownership(updated.user_id, current_user.id, "Education")
    education_response = EducationResponse.model_validate(updated)
    return success_response(
        data=education_response,
        message="Education updated successfully"
    )

@router.delete("/educations/{education_id}", response_model=SuccessResponse, tags=["Profile Education"])
@handle_errors
async def delete_education(education_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete education"""
    repo = EducationRepository(db)
    if not repo.delete_education(education_id, current_user.id):
        raise not_found_error("Education not found")
    return success_response(
        data=None,
        message="Education deleted successfully"
    )

@router.get("/experiences", response_model=SuccessResponse, tags=["Profile Experience"])
@handle_errors
async def get_my_experiences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all experiences for current user"""
    repo = ExperienceRepository(db)
    experiences = repo.get_experiences_by_user(current_user.id)
    experience_responses = [ExperienceResponse.model_validate(exp) for exp in experiences]
    return success_response(
        data=experience_responses,
        message="Experiences retrieved successfully"
    )

@router.get("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
@handle_errors
async def get_experience_by_id(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get experience by ID"""
    repo = ExperienceRepository(db)
    experience = repo.get_experience_by_id(id)
    validate_entity_exists(experience, "Experience")
    validate_ownership(experience.user_id, current_user.id, "Experience")
    experience_response = ExperienceResponse.model_validate(experience)
    return success_response(
        data=experience_response,
        message="Experience retrieved successfully"
    )

@router.post("/experiences", response_model=SuccessResponse, tags=["Profile Experience"])
@handle_errors
async def add_experience(data: ExperienceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add new experience"""
    from ..core.logging_config import logger
    from fastapi import HTTPException
    
    try:
        repo = ExperienceRepository(db)
        created_experience = repo.create_experience(current_user.id, data)
        if not created_experience:
            raise HTTPException(status_code=500, detail="Failed to create experience")
        experience_response = ExperienceResponse.model_validate(created_experience)
        return success_response(
            data=experience_response,
            message="Experience added successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding experience: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create experience")

@router.patch("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
@handle_errors
async def update_experience(id: int, data: ExperienceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update experience"""
    repo = ExperienceRepository(db)
    if hasattr(data, 'model_dump'):
        update_data = data.model_dump(exclude_unset=True)
    else:
        update_data = data.dict(exclude_unset=True)
    updated = repo.update_experience(id, update_data)
    validate_entity_exists(updated, "Experience")
    validate_ownership(updated.user_id, current_user.id, "Experience")
    experience_response = ExperienceResponse.model_validate(updated)
    return success_response(
        data=experience_response,
        message="Experience updated successfully"
    )

@router.delete("/experiences/{id}", response_model=SuccessResponse, tags=["Profile Experience"])
@handle_errors
async def delete_experience(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete experience"""
    repo = ExperienceRepository(db)
    if not repo.delete_experience(id, current_user.id):
        raise not_found_error("Experience not found")
    return success_response(
        data=None,
        message="Experience deleted successfully"
    )

@router.get("/certifications", response_model=SuccessResponse, tags=["Profile Certifications"])
@handle_errors
async def get_my_certifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all certifications for current user"""
    repo = CertificationRepository(db)
    certifications = repo.get_certifications_by_user(current_user.id)
    certification_responses = [CertificationResponse.model_validate(cert) for cert in certifications]
    return success_response(
        data=certification_responses,
        message="Certifications retrieved successfully"
    )

@router.get("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
@handle_errors
async def get_certification_by_id(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get certification by ID"""
    repo = CertificationRepository(db)
    certification = repo.get_certification_by_id(id)
    validate_entity_exists(certification, "Certification")
    validate_ownership(certification.user_id, current_user.id, "Certification")
    certification_response = CertificationResponse.model_validate(certification)
    return success_response(
        data=certification_response,
        message="Certification retrieved successfully"
    )

@router.post("/certifications", response_model=SuccessResponse, tags=["Profile Certifications"])
@handle_errors
async def add_certification(data: CertificationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Add new certification"""
    repo = CertificationRepository(db)
    created_certification = repo.create_certification(current_user.id, data)
    certification_response = CertificationResponse.model_validate(created_certification)
    return success_response(
        data=certification_response,
        message="Certification added successfully"
    )

@router.patch("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
@handle_errors
async def update_certification(id: int, data: CertificationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update certification"""
    repo = CertificationRepository(db)
    updated = repo.update_certification(id, data.dict(exclude_unset=True))
    validate_entity_exists(updated, "Certification")
    validate_ownership(updated.user_id, current_user.id, "Certification")
    certification_response = CertificationResponse.model_validate(updated)
    return success_response(
        data=certification_response,
        message="Certification updated successfully"
    )

@router.delete("/certifications/{id}", response_model=SuccessResponse, tags=["Profile Certifications"])
@handle_errors
async def delete_certification(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete certification"""
    repo = CertificationRepository(db)
    if not repo.delete_certification(id, current_user.id):
        raise not_found_error("Certification not found")
    return success_response(
        data=None,
        message="Certification deleted successfully"
    )

@router.get("/projects", response_model=SuccessResponse, tags=["Profile Projects"])
@handle_errors
async def get_my_projects(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get all projects for current user"""
    from ..core.config import settings
    
    repo = ProjectRepository(db)
    projects = repo.get_projects_by_user(current_user.id)
    project_responses = [ProjectResponse.model_validate(proj) for proj in projects]
    
    base_url = settings.BASE_URL
    
    for project_response in project_responses:
        for img in project_response.images:
            if img.image and not img.image.startswith("http"):
                img.image = f"{base_url}{img.image}"
    
    return success_response(
        data=project_responses,
        message="Projects retrieved successfully"
    )

@router.get("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
@handle_errors
async def get_project_by_id(
    id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get project by ID"""
    from ..core.config import settings
    
    repo = ProjectRepository(db)
    project = repo.get_project_by_id(id)
    validate_entity_exists(project, "Project")
    validate_ownership(project.user_id, current_user.id, "Project")
    project_response = ProjectResponse.model_validate(project)
    
    base_url = settings.BASE_URL
    
    for img in project_response.images:
        if img.image and not img.image.startswith("http"):
            img.image = f"{base_url}{img.image}"
    
    return success_response(
        data=project_response,
        message="Project retrieved successfully"
    )

@router.post("/projects", response_model=SuccessResponse, tags=["Profile Projects"])
@handle_errors
async def add_project(
    request: Request,
    project_name: str = Form(...),
    role: str = Form(None),
    from_date: str = Form(None),
    to_date: str = Form(None),
    live_project_path: str = Form(None),
    description: str = Form(None),
    images: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add new project"""
    from datetime import datetime
    import os
    from ..models.project_image import ProjectImage
    from ..core.logging_config import logger
    from fastapi import HTTPException

    from_date_parsed = None
    to_date_parsed = None
    
    try:
        if from_date:
            from_date_parsed = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid from_date format: {from_date}, error: {e}")
        from_date_parsed = None
    
    try:
        if to_date:
            to_date_parsed = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        logger.warning(f"Invalid to_date format: {to_date}, error: {e}")
        to_date_parsed = None

    project_data = {
        "project_name": project_name,
        "role": role,
        "from_date": from_date_parsed,
        "to_date": to_date_parsed,
        "live_project_path": live_project_path,
        "description": description
    }

    try:
        repo = ProjectRepository(db)
        project = repo.create_project(current_user.id, project_data)
    except Exception as e:
        logger.error(f"Error creating project in repository: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Couldn't save projects")

    if images:
        try:
            upload_dir = "static/projects"
            os.makedirs(upload_dir, exist_ok=True)
            
            for img in images:
                if img and img.content_type and img.content_type.startswith('image/'):
                    try:
                        filename = f"{project.id}_{img.filename}"
                        file_path = os.path.join(upload_dir, filename)
                        with open(file_path, "wb") as buffer:
                            content = await img.read()
                            buffer.write(content)
                        normalized_path = file_path.replace('\\', '/')
                        rel_path = f"/{normalized_path}"
                        
                        image_obj = ProjectImage(project_id=project.id, image=rel_path)
                        db.add(image_obj)
                    except Exception as e:
                        logger.error(f"Error uploading image {img.filename}: {e}", exc_info=True)
            
            db.commit()
            db.refresh(project)
        except Exception as e:
            logger.error(f"Error handling project images: {e}", exc_info=True)
            db.rollback()

    try:
        project_response = ProjectResponse.model_validate(project)
        
        if request:
            base_url = str(request.base_url).rstrip("/")
            for img in project_response.images:
                if img.image and not img.image.startswith("http"):
                    img.image = f"{base_url}{img.image}"
        else:
            from ..core.config import settings
            base_url = settings.BASE_URL
            for img in project_response.images:
                if img.image and not img.image.startswith("http"):
                    img.image = f"{base_url}{img.image}"

        return success_response(
            data=project_response,
            message="Project added successfully"
        )
    except Exception as e:
        logger.error(f"Error creating project response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Couldn't save projects")

@router.patch("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
@handle_errors
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
    db: Session = Depends(get_db)
):
    """Update project"""
    from datetime import datetime
    import os
    from ..models.project_image import ProjectImage
    
    repo = ProjectRepository(db)
    
    project = repo.get_project_by_id(id)
    validate_entity_exists(project, "Project")
    validate_ownership(project.user_id, current_user.id, "Project")
    
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
    
    if images:
        image_urls = []
        upload_dir = "static/projects"
        os.makedirs(upload_dir, exist_ok=True)
        
        for img in images:
            if img.content_type.startswith('image/'):
                filename = f"{project.id}_{img.filename}"
                file_path = os.path.join(upload_dir, filename)
                with open(file_path, "wb") as buffer:
                    content = await img.read()
                    buffer.write(content)
                normalized_path = file_path.replace('\\', '/')
                rel_path = f"/{normalized_path}"
                image_urls.append(rel_path)
        
        if image_urls:
            update_data['images'] = image_urls
    
    updated = repo.update_project(id, update_data)
    validate_entity_exists(updated, "Project")
    
    project_response = ProjectResponse.model_validate(updated)
    
    base_url = str(request.base_url).rstrip("/")
    for img in project_response.images:
        if img.image and not img.image.startswith("http"):
            img.image = f"{base_url}{img.image}"
    
    return success_response(
        data=project_response,
        message="Project updated successfully"
    )

@router.delete("/projects/{id}", response_model=SuccessResponse, tags=["Profile Projects"])
@handle_errors
async def delete_project(id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete project"""
    repo = ProjectRepository(db)
    if not repo.delete_project(id, current_user.id):
        raise not_found_error("Project not found")
    return success_response(
        data=None,
        message="Project deleted successfully"
    )

@router.patch("/avatar", response_model=SuccessResponse, tags=["Profile Avatar Upload and Update"])
@handle_errors
async def upload_avatar(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Upload user avatar"""
    if not file.content_type.startswith('image/'):
        raise bad_request_error("Only images allowed")
    upload_dir = "static/avatars"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{current_user.id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    normalized_path = file_path.replace('\\', '/')
    current_user.avatar_url = f"/{normalized_path}"
    db.commit()
    db.refresh(current_user)
    user_response = UserFullResponse.model_validate(current_user)
    return success_response(
        data=user_response,
        message="Avatar uploaded successfully"
    )

@router.post("/language", response_model=SuccessResponse, tags=["Profile Language"])
@handle_errors
async def update_user_language(data: UserLanguageUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user language"""
    language_repo = LanguageRepository(db)
    language = language_repo.get(data.language_id)
    validate_entity_exists(language, "Language")

    current_user.language_id = data.language_id
    db.commit()
    db.refresh(current_user)

    user_response = UserFullResponse.model_validate(current_user)
    return success_response(
        data=user_response,
        message="Language updated successfully"
    )

@router.get("/categories", response_model=SuccessResponse, tags=["Profile Categories"])
@handle_errors
async def get_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all main categories"""
    repo = CategoryRepository(db)
    categories = repo.get_categories_only_with_filter(is_active=True)
    category_responses = [CategoryResponse.model_validate(cat) for cat in categories]
    return success_response(
        data=category_responses,
        message="Categories retrieved successfully"
    )

@router.get("/categories/{category_id}/subcategories", response_model=SuccessResponse, tags=["Profile Categories"])
@handle_errors
async def get_subcategories(category_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get subcategories for a specific main category"""
    repo = CategoryRepository(db)
    subcategories = repo.get_subcategories_with_filter(category_id, is_active=True)
    subcategory_responses = [CategoryResponse.model_validate(sub) for sub in subcategories]
    return success_response(
        data=subcategory_responses,
        message="Subcategories retrieved successfully"
    )

@router.patch("/categories", response_model=SuccessResponse, tags=["Profile Categories"])
@handle_errors
async def update_user_categories(
    main_category_id: Optional[int] = None,
    sub_category_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's main category and sub-category"""
    repo = UserRepository(db)
    updated_user = repo.update_user_categories(
        current_user.id, 
        main_category_id=main_category_id, 
        sub_category_id=sub_category_id
    )
    validate_entity_exists(updated_user, "User")
    
    user_response = UserFullResponse.model_validate(updated_user)
    return success_response(
        data=user_response,
        message="Categories updated successfully"
    )

@router.get("/my-categories", response_model=SuccessResponse, tags=["Profile Categories"])
@handle_errors
async def get_my_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's categories"""
    user_response = UserFullResponse.model_validate(current_user)
    categories_data = {
        "main_category": user_response.main_category,
        "sub_category": user_response.sub_category
    }
    return success_response(
        data=categories_data,
        message="User categories retrieved successfully"
    ) 