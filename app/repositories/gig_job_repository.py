from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.gig_job import GigJob
from app.models.skill import Skill
from app.schemas.gig_job import GigJobCreate, GigJobUpdate
from app.pagination import PaginationParams


class GigJobRepository:
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

    def _prepare_gig_job_response(self, gig_job: GigJob) -> dict:
        """Prepare gig job data for response with skills"""
        # Convert skills to dict format
        skills_data = []
        
        for skill in gig_job.skills:
            skills_data.append({
                "id": skill.id,
                "name": skill.name,
                "created_at": skill.created_at,
                "updated_at": skill.updated_at,
                "is_deleted": skill.is_deleted
            })
        
        # Create response data
        response_data = {
            "id": gig_job.id,
            "title": gig_job.title,
            "description": gig_job.description,
            "location": gig_job.location,
            "experience_level": gig_job.experience_level,
            "job_type": gig_job.job_type,
            "work_mode": gig_job.work_mode,
            "remote_only": gig_job.remote_only,
            "min_salary": gig_job.min_salary,
            "max_salary": gig_job.max_salary,
            "deadline_days": gig_job.deadline_days,
            "status": gig_job.status,
            "author_id": gig_job.author_id,
            "created_at": gig_job.created_at,
            "updated_at": gig_job.updated_at,
            "skills": skills_data
        }
        
        return response_data

    def create(self, gig_job_data: GigJobCreate, author_id: int) -> dict:
        """Create a new gig job with skills"""
        # Extract skill_names from the data
        skill_names = gig_job_data.skill_names
        gig_job_dict = gig_job_data.model_dump(exclude={'skill_names'})
        
        # Create the gig job
        db_gig_job = GigJob(
            **gig_job_dict,
            author_id=author_id
        )
        self.db.add(db_gig_job)
        self.db.flush()  # Flush to get the ID
        
        # Get or create skills and add them to the gig job
        if skill_names:
            skills = self._get_or_create_skills(skill_names)
            db_gig_job.skills = skills
        
        self.db.commit()
        self.db.refresh(db_gig_job)
        
        # Return prepared response data
        return self._prepare_gig_job_response(db_gig_job)

    def get_by_id(self, gig_job_id: int) -> Optional[dict]:
        """Get gig job by ID with skills"""
        gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.skills)
        ).filter(GigJob.id == gig_job_id).first()
        
        if gig_job:
            return self._prepare_gig_job_response(gig_job)
        return None

    def get_user_gig_jobs(self, user_id: int, pagination: PaginationParams) -> tuple[List[dict], int]:
        """Get paginated gig jobs for a specific user with skills"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills)
        ).filter(GigJob.author_id == user_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total
    
    def get_user_gig_jobs_with_filters(
        self, 
        user_id: int, 
        pagination: PaginationParams, 
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        work_mode: Optional[str] = None,
        remote_only: Optional[bool] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        location: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """Get filtered gig jobs for a specific user"""
        query = self.db.query(GigJob).filter(GigJob.author_id == user_id)
        
        if status:
            query = query.filter(GigJob.status == status)
        
        if job_type:
            query = query.filter(GigJob.job_type == job_type)
            
        if experience_level:
            query = query.filter(GigJob.experience_level == experience_level)
            
        if work_mode:
            query = query.filter(GigJob.work_mode == work_mode)
            
        if remote_only is not None:
            query = query.filter(GigJob.remote_only == remote_only)
            
        if min_salary is not None:
            query = query.filter(GigJob.min_salary >= min_salary)
            
        if max_salary is not None:
            query = query.filter(GigJob.max_salary <= max_salary)
            
        if location:
            query = query.filter(GigJob.location.ilike(f"%{location}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            # Load skills for each gig job
            self.db.refresh(gig_job)
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total

    def get_all_gig_jobs(
        self, 
        pagination: PaginationParams, 
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        work_mode: Optional[str] = None,
        remote_only: Optional[bool] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        location: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """Get all gig jobs with multiple filters"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills)
        )
        
        if status:
            query = query.filter(GigJob.status == status)
        
        if job_type:
            query = query.filter(GigJob.job_type == job_type)
            
        if experience_level:
            query = query.filter(GigJob.experience_level == experience_level)
            
        if work_mode:
            query = query.filter(GigJob.work_mode == work_mode)
            
        if remote_only is not None:
            query = query.filter(GigJob.remote_only == remote_only)
            
        if min_salary is not None:
            query = query.filter(GigJob.min_salary >= min_salary)
            
        if max_salary is not None:
            query = query.filter(GigJob.max_salary <= max_salary)
            
        if location:
            query = query.filter(GigJob.location.ilike(f"%{location}%"))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total

    def update(self, gig_job_id: int, gig_job_data: GigJobUpdate, user_id: int) -> Optional[dict]:
        """Update gig job with skills (only by author)"""
        gig_job = self.db.query(GigJob).filter(
            and_(GigJob.id == gig_job_id, GigJob.author_id == user_id)
        ).first()
        
        if not gig_job:
            return None
        
        update_data = gig_job_data.model_dump(exclude_unset=True)
        
        # Handle skills separately
        skill_names = update_data.pop('skill_names', None)
        
        # Update other fields
        for field, value in update_data.items():
            setattr(gig_job, field, value)
        
        # Update skills if provided
        if skill_names is not None:
            skills = self._get_or_create_skills(skill_names)
            gig_job.skills = skills
        
        self.db.commit()
        self.db.refresh(gig_job)
        
        # Return prepared response data
        return self._prepare_gig_job_response(gig_job)

    def delete(self, gig_job_id: int, user_id: int) -> bool:
        """Delete gig job (only by author)"""
        gig_job = self.db.query(GigJob).filter(
            and_(GigJob.id == gig_job_id, GigJob.author_id == user_id)
        ).first()
        
        if not gig_job:
            return False
        
        self.db.delete(gig_job)
        self.db.commit()
        return True

    def search_gig_jobs(self, search_term: str, pagination: PaginationParams) -> tuple[List[dict], int]:
        """Search gig jobs by title, description, or skills"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills)
        ).filter(
            or_(
                GigJob.title.ilike(f"%{search_term}%"),
                GigJob.description.ilike(f"%{search_term}%")
            )
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total
