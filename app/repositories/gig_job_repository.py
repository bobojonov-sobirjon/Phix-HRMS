from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.gig_job import GigJob
from app.models.skill import Skill
from app.schemas.gig_job import GigJobCreate, GigJobUpdate
from app.pagination import PaginationParams
from app.config import settings


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
        """Prepare gig job data for response with skills and category info"""
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
        
        # Get proposal count
        proposal_count = len(gig_job.proposals) if gig_job.proposals else 0
        
        # Create response data
        response_data = {
            "id": gig_job.id,
            "title": gig_job.title,
            "description": gig_job.description,
            "location_id": gig_job.location_id,
            "location": {
                "id": gig_job.location.id,
                "name": gig_job.location.name,
                "flag_image": f"{settings.BASE_URL}{gig_job.location.flag_image}" if gig_job.location.flag_image and not gig_job.location.flag_image.startswith(('http://', 'https://')) else gig_job.location.flag_image,
                "code": gig_job.location.code,
                "created_at": gig_job.location.created_at,
                "updated_at": gig_job.location.updated_at,
                "is_deleted": gig_job.location.is_deleted
            } if gig_job.location else None,
            "experience_level": gig_job.experience_level.value if hasattr(gig_job.experience_level, 'value') else str(gig_job.experience_level),
            "job_type": gig_job.job_type.value if hasattr(gig_job.job_type, 'value') else str(gig_job.job_type),
            "work_mode": gig_job.work_mode.value if hasattr(gig_job.work_mode, 'value') else str(gig_job.work_mode),
            "remote_only": gig_job.remote_only,
            "min_salary": gig_job.min_salary,
            "max_salary": gig_job.max_salary,
            "deadline_days": gig_job.deadline_days,
            "status": gig_job.status.value if hasattr(gig_job.status, 'value') else str(gig_job.status),
            "author_id": gig_job.author_id,
            "category_id": gig_job.category_id,
            "category_name": gig_job.category.name if gig_job.category else None,
            "man_category": {
                "id": gig_job.category.id,
                "name": gig_job.category.name,
                "description": gig_job.category.description,
                "is_active": gig_job.category.is_active,
                "created_at": gig_job.category.created_at,
                "updated_at": gig_job.category.updated_at
            } if gig_job.category else None,
            "subcategory_id": gig_job.subcategory_id,
            "subcategory_name": gig_job.subcategory.name if gig_job.subcategory else None,
            "sub_category": {
                "id": gig_job.subcategory.id,
                "name": gig_job.subcategory.name,
                "description": gig_job.subcategory.description,
                "is_active": gig_job.subcategory.is_active,
                "created_at": gig_job.subcategory.created_at,
                "updated_at": gig_job.subcategory.updated_at
            } if gig_job.subcategory else None,
            "created_at": gig_job.created_at,
            "updated_at": gig_job.updated_at,
            "skills": skills_data,
            "proposal_count": proposal_count
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
        
        # Load category, subcategory, location and proposals relationships
        self.db.refresh(db_gig_job, ['category', 'subcategory', 'location', 'proposals'])
        
        # Return prepared response data
        return self._prepare_gig_job_response(db_gig_job)

    def get_by_id(self, gig_job_id: int) -> Optional[dict]:
        """Get gig job by ID with skills and category info"""
        gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.skills),
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.proposals)
        ).filter(GigJob.id == gig_job_id).first()
        
        if gig_job:
            return self._prepare_gig_job_response(gig_job)
        return None

    def get_object_by_id(self, gig_job_id: int) -> Optional[GigJob]:
        """Get gig job object by ID (for internal use)"""
        return self.db.query(GigJob).filter(GigJob.id == gig_job_id).first()

    def get_user_gig_jobs(self, user_id: int, pagination: PaginationParams) -> tuple[List[dict], int]:
        """Get paginated gig jobs for a specific user with skills and category info"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills),
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.proposals)
        ).filter(GigJob.author_id == user_id).order_by(GigJob.created_at.desc())
        
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
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        project_length: Optional[str] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """Get filtered gig jobs for a specific user with category info"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills),
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.proposals)
        ).filter(GigJob.author_id == user_id)
        
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
            
        if location_id:
            query = query.filter(GigJob.location_id == location_id)
            
        if category_id:
            query = query.filter(GigJob.category_id == category_id)
            
        if subcategory_id:
            query = query.filter(GigJob.subcategory_id == subcategory_id)
            
        if project_length:
            if project_length == "less_than_one_month":
                query = query.filter(GigJob.deadline_days <= 30)
            elif project_length == "one_to_three_months":
                query = query.filter(GigJob.deadline_days.between(31, 90))
            elif project_length == "three_to_six_months":
                query = query.filter(GigJob.deadline_days.between(91, 180))
            elif project_length == "more_than_six_months":
                query = query.filter(GigJob.deadline_days > 180)
                
        if date_posted and date_posted != "any_time":
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(days=7))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        # Apply sorting
        if sort_by == "most_relevant":
            # For now, we'll use created_at desc as relevance
            # In the future, this could be enhanced with more sophisticated relevance scoring
            query = query.order_by(GigJob.created_at.desc())
        else:  # most_recent (default)
            query = query.order_by(GigJob.created_at.desc())
        
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
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        project_length: Optional[str] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> tuple[List[dict], int]:
        """Get all gig jobs with multiple filters and category info"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills),
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.proposals)
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
            
        if location_id:
            query = query.filter(GigJob.location_id == location_id)
            
        if category_id:
            query = query.filter(GigJob.category_id == category_id)
            
        if subcategory_id:
            query = query.filter(GigJob.subcategory_id == subcategory_id)
            
        if project_length:
            if project_length == "less_than_one_month":
                query = query.filter(GigJob.deadline_days <= 30)
            elif project_length == "one_to_three_months":
                query = query.filter(GigJob.deadline_days.between(31, 90))
            elif project_length == "three_to_six_months":
                query = query.filter(GigJob.deadline_days.between(91, 180))
            elif project_length == "more_than_six_months":
                query = query.filter(GigJob.deadline_days > 180)
                
        if date_posted and date_posted != "any_time":
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(days=7))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        # Apply sorting
        if sort_by == "most_relevant":
            # For now, we'll use created_at desc as relevance
            # In the future, this could be enhanced with more sophisticated relevance scoring
            query = query.order_by(GigJob.created_at.desc())
        else:  # most_recent (default)
            query = query.order_by(GigJob.created_at.desc())
        
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
        
        # Load category, subcategory, location and proposals relationships
        self.db.refresh(gig_job, ['category', 'subcategory', 'location', 'proposals'])
        
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
        """Search gig jobs by title, description, or skills with category info"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.skills),
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.proposals)
        ).filter(
            or_(
                GigJob.title.ilike(f"%{search_term}%"),
                GigJob.description.ilike(f"%{search_term}%")
            )
        ).order_by(GigJob.created_at.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total
