from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.full_time_job import FullTimeJob
from ..models.corporate_profile import CorporateProfile
from ..models.skill import Skill
from ..schemas.full_time_job import FullTimeJobCreate, FullTimeJobUpdate


class FullTimeJobRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_or_create_skills(self, skill_names: List[str]) -> List[Skill]:
        """Get existing skills or create new ones if they don't exist"""
        skills = []
        for skill_name in skill_names:
            if skill_name.strip():  # Skip empty strings
                # Check if skill exists
                skill = self.db.query(Skill).filter(
                    Skill.name.ilike(skill_name.strip())
                ).first()
                
                if not skill:
                    # Create new skill
                    skill = Skill(name=skill_name.strip())
                    self.db.add(skill)
                    self.db.flush()  # Flush to get the ID
                
                skills.append(skill)
        
        return skills
    
    def _prepare_full_time_job_response(self, job: FullTimeJob) -> dict:
        """Prepare full-time job data for response with skills"""
        # Convert skills to dict format
        skills_data = []
        
        for skill in job.skills:
            skills_data.append({
                "id": skill.id,
                "name": skill.name,
                "created_at": skill.created_at,
                "updated_at": skill.updated_at,
                "is_deleted": skill.is_deleted
            })
        
        # Create response data
        response_data = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "responsibilities": job.responsibilities,
            "location": job.location,
            "job_type": job.job_type,
            "work_mode": job.work_mode,
            "experience_level": job.experience_level,
            "min_salary": job.min_salary,
            "max_salary": job.max_salary,
            "status": job.status,
            "company_id": job.company_id,
            "company_name": job.company.company_name if job.company else None,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "skills": skills_data
        }
        
        return response_data
    
    def create(self, full_time_job: FullTimeJobCreate, company_id: int) -> dict:
        """Create a new full-time job with skills"""
        # Extract skill_names from the data
        skill_names = full_time_job.skill_names
        job_dict = full_time_job.model_dump(exclude={'skill_names'})
        
        # Create the job
        db_job = FullTimeJob(
            **job_dict,
            company_id=company_id
        )
        self.db.add(db_job)
        self.db.flush()  # Flush to get the ID
        
        # Get or create skills and add them to the job
        if skill_names:
            skills = self._get_or_create_skills(skill_names)
            db_job.skills = skills
        
        self.db.commit()
        self.db.refresh(db_job)
        
        # Load company relationship for response
        db_job.company = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == company_id
        ).first()
        
        # Return prepared response data
        return self._prepare_full_time_job_response(db_job)
    
    def get_by_id(self, job_id: int) -> Optional[dict]:
        """Get full-time job by ID with skills"""
        job = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(
            FullTimeJob.id == job_id
        ).first()
        
        if job:
            return self._prepare_full_time_job_response(job)
        return None
    
    def get_by_company_id(self, company_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all jobs by company ID"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(
            FullTimeJob.company_id == company_id
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all jobs by user ID (through corporate profile)"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).join(
            CorporateProfile, FullTimeJob.company_id == CorporateProfile.id
        ).filter(
            CorporateProfile.user_id == user_id
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def get_all_active(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all active full-time jobs"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(
            FullTimeJob.status == "active"
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all full-time jobs with pagination"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def update(self, job_id: int, full_time_job: FullTimeJobUpdate) -> Optional[dict]:
        """Update full-time job with skills"""
        db_job = self.db.query(FullTimeJob).filter(FullTimeJob.id == job_id).first()
        if not db_job:
            return None
        
        update_data = full_time_job.model_dump(exclude_unset=True)
        
        # Handle skills separately
        skill_names = update_data.pop('skill_names', None)
        
        # Update other fields
        for field, value in update_data.items():
            setattr(db_job, field, value)
        
        # Update skills if provided
        if skill_names is not None:
            skills = self._get_or_create_skills(skill_names)
            db_job.skills = skills
        
        self.db.commit()
        self.db.refresh(db_job)
        
        # Load company relationship for response
        db_job.company = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == db_job.company_id
        ).first()
        
        # Return prepared response data
        return self._prepare_full_time_job_response(db_job)
    
    def delete(self, job_id: int) -> bool:
        """Delete full-time job"""
        db_job = self.get_by_id(job_id)
        if not db_job:
            return False
        
        self.db.delete(db_job)
        self.db.commit()
        return True
    
    def change_status(self, job_id: int, status: str) -> Optional[dict]:
        """Change job status"""
        db_job = self.db.query(FullTimeJob).filter(FullTimeJob.id == job_id).first()
        if not db_job:
            return None
        
        db_job.status = status
        self.db.commit()
        self.db.refresh(db_job)
        
        # Load company relationship for response
        db_job.company = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == db_job.company_id
        ).first()
        
        # Return prepared response data
        return self._prepare_full_time_job_response(db_job)
    
    def search_jobs(self, 
                   title: Optional[str] = None,
                   location: Optional[str] = None,
                   experience_level: Optional[str] = None,
                   work_mode: Optional[str] = None,
                   min_salary: Optional[float] = None,
                   max_salary: Optional[float] = None,
                   skip: int = 0,
                   limit: int = 100) -> List[dict]:
        """Search jobs with filters"""
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(FullTimeJob.status == "active")
        
        if title:
            query = query.filter(FullTimeJob.title.ilike(f"%{title}%"))
        
        if location:
            query = query.filter(FullTimeJob.location.ilike(f"%{location}%"))
        
        if experience_level:
            query = query.filter(FullTimeJob.experience_level == experience_level)
        
        if work_mode:
            query = query.filter(FullTimeJob.work_mode == work_mode)
        
        if min_salary is not None:
            query = query.filter(FullTimeJob.max_salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(FullTimeJob.min_salary <= max_salary)
        
        jobs = query.offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def count_total(self) -> int:
        """Get total count of full-time jobs"""
        return self.db.query(FullTimeJob).count()
    
    def count_active(self) -> int:
        """Get count of active full-time jobs"""
        return self.db.query(FullTimeJob).filter(
            FullTimeJob.status == "active"
        ).count()
    
    def count_by_company(self, company_id: int) -> int:
        """Get count of jobs by company"""
        return self.db.query(FullTimeJob).filter(
            FullTimeJob.company_id == company_id
        ).count()
    
    def count_by_user(self, user_id: int) -> int:
        """Get count of jobs by user"""
        return self.db.query(FullTimeJob).join(
            CorporateProfile, FullTimeJob.company_id == CorporateProfile.id
        ).filter(
            CorporateProfile.user_id == user_id
        ).count()
    
    def get_by_user_id_with_filters(self, 
                                   user_id: int, 
                                   skip: int = 0, 
                                   limit: int = 100,
                                   status: Optional[str] = None,
                                   job_type: Optional[str] = None,
                                   experience_level: Optional[str] = None,
                                   work_mode: Optional[str] = None,
                                   location: Optional[str] = None,
                                   min_salary: Optional[float] = None,
                                   max_salary: Optional[float] = None) -> List[dict]:
        """Get filtered jobs by user ID with skills"""
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).join(
            CorporateProfile, FullTimeJob.company_id == CorporateProfile.id
        ).filter(
            CorporateProfile.user_id == user_id
        )
        
        if status:
            query = query.filter(FullTimeJob.status == status)
        
        if job_type:
            query = query.filter(FullTimeJob.job_type == job_type)
        
        if experience_level:
            query = query.filter(FullTimeJob.experience_level == experience_level)
        
        if work_mode:
            query = query.filter(FullTimeJob.work_mode == work_mode)
        
        if location:
            query = query.filter(FullTimeJob.location.ilike(f"%{location}%"))
        
        if min_salary is not None:
            query = query.filter(FullTimeJob.max_salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(FullTimeJob.min_salary <= max_salary)
        
        jobs = query.offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job))
        
        return prepared_jobs
    
    def count_by_user_with_filters(self, 
                                  user_id: int,
                                  status: Optional[str] = None,
                                  job_type: Optional[str] = None,
                                  experience_level: Optional[str] = None,
                                  work_mode: Optional[str] = None,
                                  location: Optional[str] = None,
                                  min_salary: Optional[float] = None,
                                  max_salary: Optional[float] = None) -> int:
        """Get filtered count of jobs by user ID"""
        query = self.db.query(FullTimeJob).join(
            CorporateProfile, FullTimeJob.company_id == CorporateProfile.id
        ).filter(
            CorporateProfile.user_id == user_id
        )
        
        if status:
            query = query.filter(FullTimeJob.status == status)
        
        if job_type:
            query = query.filter(FullTimeJob.job_type == job_type)
        
        if experience_level:
            query = query.filter(FullTimeJob.experience_level == experience_level)
        
        if work_mode:
            query = query.filter(FullTimeJob.work_mode == work_mode)
        
        if location:
            query = query.filter(FullTimeJob.location.ilike(f"%{location}%"))
        
        if min_salary is not None:
            query = query.filter(FullTimeJob.max_salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(FullTimeJob.min_salary <= max_salary)
        
        return query.count()
