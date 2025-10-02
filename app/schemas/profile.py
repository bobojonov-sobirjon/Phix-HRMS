from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pydantic import computed_field
from ..config import settings
from .category import CategoryResponse

class LocationBase(BaseModel):
    name: str
    flag_image: Optional[str] = None
    code: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    name: Optional[str] = None
    flag_image: Optional[str] = None
    code: Optional[str] = None

class LocationResponse(LocationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SkillBase(BaseModel):
    name: str

class SkillCreate(SkillBase):
    pass

class SkillUpdate(SkillBase):
    name: Optional[str] = None

class SkillResponse(SkillBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EducationBase(BaseModel):
    degree: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    is_graduate: bool = False
    description: Optional[str] = None
    school_name: Optional[str] = None

class EducationCreate(EducationBase):
    education_facility_id: Optional[int] = None

class EducationUpdate(EducationBase):
    degree: Optional[str] = None
    school_name: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    is_graduate: Optional[bool] = None
    description: Optional[str] = None
    education_facility_id: Optional[int] = None

class EducationFacilityResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EducationResponse(EducationBase):
    id: int
    user_id: int
    education_facility_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    education_facility: Optional[EducationFacilityResponse] = None
    class Config:
        from_attributes = True

class ExperienceBase(BaseModel):
    job_title: str
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    is_current: bool = False
    industry: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceUpdate(ExperienceBase):
    job_title: Optional[str] = None
    company: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    is_current: Optional[bool] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    job_type: Optional[str] = None

class ExperienceResponse(ExperienceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    company_ref: Optional["CompanyResponse"] = None
    class Config:
        from_attributes = True

class CertificationCenterResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CertificationBase(BaseModel):
    title: str
    publishing_organization: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    certificate_id: Optional[str] = None
    certification_url: Optional[str] = None
    certificate_path: Optional[str] = None
    certification_center_id: Optional[int] = None
    center_name: Optional[str] = None

class CertificationCreate(CertificationBase):
    pass

class CertificationUpdate(CertificationBase):
    title: Optional[str] = None
    publishing_organization: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    certificate_id: Optional[str] = None
    certificate_path: Optional[str] = None

class CertificationResponse(CertificationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    certification_center: Optional[CertificationCenterResponse] = None
    class Config:
        from_attributes = True

class ProjectImageBase(BaseModel):
    image: str

class ProjectImageCreate(ProjectImageBase):
    pass

class ProjectImageResponse(ProjectImageBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    project_name: str
    role: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    live_project_path: Optional[str] = None
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    images: List[str] = []

class ProjectUpdate(ProjectBase):
    project_name: Optional[str] = None
    role: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    live_project_path: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None

class ProjectResponse(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    images: List[ProjectImageResponse] = []

    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class LanguageResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class UserShortDetails(BaseModel):
    """Short user details for proposals and other lightweight responses"""
    id: int
    name: str
    email: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    current_position: Optional[str] = None
    location: Optional[LocationResponse] = None
    main_category: Optional[CategoryResponse] = None
    sub_category: Optional[CategoryResponse] = None
    skills: List[SkillResponse] = []

    class Config:
        from_attributes = True

class UserFullResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    is_verified: bool
    is_social_user: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None
    main_category_id: Optional[int] = None
    sub_category_id: Optional[int] = None
    roles: List[RoleResponse] = []
    location: Optional[LocationResponse] = None
    main_category: Optional[CategoryResponse] = None
    sub_category: Optional[CategoryResponse] = None
    skills: List[SkillResponse] = []
    educations: List[EducationResponse] = []
    experiences: List[ExperienceResponse] = []
    certifications: List[CertificationResponse] = []
    projects: List[ProjectResponse] = []
    language_id: Optional[int] = None
    language: Optional[LanguageResponse] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    about_me: Optional[str] = None
    current_position: Optional[str] = None
    location_id: Optional[int] = None
    language_id: Optional[int] = None
    main_category_id: Optional[int] = None
    sub_category_id: Optional[int] = None

class UserSkillBase(BaseModel):
    user_id: int
    skill_id: int

class UserSkillCreateWithoutUser(BaseModel):
    skill_id: int

class UserSkillCreateBySkillName(BaseModel):
    skill_names: List[str]

class UserSkillCreateBySkillId(BaseModel):
    skill_ids: List[int]

class UserSkillCreate(UserSkillBase):
    pass

class UserSkillResponse(UserSkillBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserSkillWithDetailsResponse(BaseModel):
    id: int
    skill_details: SkillResponse
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CompanyResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class CompanyCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    country: Optional[str] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    country: Optional[str] = None

class UserLanguageUpdate(BaseModel):
    language_id: int 