from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, text
from datetime import datetime, timedelta
from ..models.gig_job import GigJob
from ..models.skill import Skill
from ..models.gig_job_skill import GigJobSkill
from ..models.category import Category
from ..models.location import Location
from ..models.user import User
from ..models.proposal import Proposal
from ..schemas.gig_job import GigJobCreate, GigJobUpdate
from ..schemas.location import Location as LocationSchema
from ..pagination import PaginationParams
from ..config import settings


class GigJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def _get_skills_by_ids(self, skill_ids: List[int]) -> List[Skill]:
        """Get skills by their IDs"""
        return self.db.query(Skill).filter(
            Skill.id.in_(skill_ids),
            Skill.is_deleted == False
        ).all()

    def create(self, gig_job_data: GigJobCreate, author_id: int) -> dict:
        """Create a new gig job"""
        # Extract skill_ids for separate handling
        skill_ids = gig_job_data.skill_ids
        
        # Create gig job data dict without skills
        gig_job_dict = gig_job_data.model_dump(exclude={'skill_ids'})
        
        # Create the gig job
        db_gig_job = GigJob(
            **gig_job_dict,
            author_id=author_id
        )
        self.db.add(db_gig_job)
        self.db.flush()  # Flush to get the ID
        
        # Get skills by IDs and add them to the gig job (no duplicates)
        if skill_ids:
            skills = self._get_skills_by_ids(skill_ids)
            # Remove duplicates by converting to set and back to list
            unique_skills = list(dict.fromkeys(skills))  # Preserves order while removing duplicates
            db_gig_job.skills = unique_skills
        
        self.db.commit()
        self.db.refresh(db_gig_job)
        
        # Load category, subcategory, location and proposals relationships
        db_gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.id == db_gig_job.id).first()
        
        return self._prepare_gig_job_response(db_gig_job)

    def get_by_id(self, gig_job_id: int) -> Optional[dict]:
        """Get a gig job by ID"""
        gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(
            GigJob.id == gig_job_id,
            GigJob.is_deleted == False
        ).first()
        
        if not gig_job:
            return None
        
        return self._prepare_gig_job_response(gig_job)

    def get_user_gig_jobs(self, user_id: int, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Get gig jobs posted by a specific user"""
        base_query = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        ).order_by(desc(GigJob.created_at))
        
        # Get total count
        total = base_query.count()
        
        # Apply pagination
        gig_jobs = base_query.offset(pagination.offset).limit(pagination.limit).all()
        
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
        experience_level: Optional[str] = None,
        project_length: Optional[str] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = "most_recent"
    ) -> Tuple[List[dict], int]:
        """Get user's gig jobs with advanced filtering"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        )
        
        # Apply filters
        if status:
            query = query.filter(GigJob.status == status)
        
        if experience_level:
            query = query.filter(GigJob.experience_level == experience_level)
        
        if project_length:
            query = query.filter(GigJob.project_length == project_length)
        
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
        
        # Date filter
        if date_posted:
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(weeks=1))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        # Sorting
        if sort_by == "most_recent":
            query = query.order_by(desc(GigJob.created_at))
        else:  # most_relevant or default
            query = query.order_by(desc(GigJob.created_at))
        
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
        """Update a gig job"""
        gig_job = self.db.query(GigJob).filter(
            GigJob.id == gig_job_id,
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        ).first()
        
        if not gig_job:
            return None
        
        # Extract skill_ids for separate handling
        skill_ids = gig_job_data.skill_ids
        
        # Update other fields
        update_data = gig_job_data.model_dump(exclude_unset=True, exclude={'skill_ids'})
        
        # Update fields
        gig_job.updated_at = func.now()
        
        # Update other fields
        for field, value in update_data.items():
            setattr(gig_job, field, value)
        
        # Update skills if provided - add new skills without removing existing ones
        if skill_ids is not None:
            new_skills = self._get_skills_by_ids(skill_ids)
            # Get existing skills
            existing_skills = list(gig_job.skills)
            # Add only new skills that don't already exist
            for new_skill in new_skills:
                if new_skill not in existing_skills:
                    existing_skills.append(new_skill)
            gig_job.skills = existing_skills
        
        self.db.commit()
        self.db.refresh(gig_job)
        
        # Load category, subcategory, location and proposals relationships
        gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.id == gig_job_id).first()
        
        return self._prepare_gig_job_response(gig_job)

    def delete(self, gig_job_id: int, user_id: int) -> bool:
        """Soft delete a gig job"""
        gig_job = self.db.query(GigJob).filter(
            GigJob.id == gig_job_id,
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        ).first()
        
        if not gig_job:
            return False
        
        gig_job.is_deleted = True
        gig_job.updated_at = func.now()
        self.db.commit()
        
        return True

    def get_all_gig_jobs(
        self, 
        pagination: PaginationParams,
        status: Optional[str] = None,
        experience_level: Optional[str] = None,
        project_length: Optional[str] = None,
        min_salary: Optional[float] = None,
        max_salary: Optional[float] = None,
        location_id: Optional[int] = None,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        date_posted: Optional[str] = None,
        sort_by: Optional[str] = "most_recent"
    ) -> Tuple[List[dict], int]:
        """Get all gig jobs with advanced filtering"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.is_deleted == False)
        
        # Apply filters
        if status:
            query = query.filter(GigJob.status == status)
        
        if experience_level:
            query = query.filter(GigJob.experience_level == experience_level)
        
        if project_length:
            query = query.filter(GigJob.project_length == project_length)
        
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
        
        # Date filter
        if date_posted:
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(weeks=1))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        # Sorting
        if sort_by == "most_recent":
            query = query.order_by(desc(GigJob.created_at))
        else:  # most_relevant or default
            query = query.order_by(desc(GigJob.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # Prepare response data for each gig job
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job))
        
        return prepared_gig_jobs, total

    def _prepare_gig_job_response(self, gig_job: GigJob) -> dict:
        """Prepare gig job response data"""
        # Count proposals for this gig job
        proposal_count = self.db.query(Proposal).filter(
            Proposal.gig_job_id == gig_job.id,
            Proposal.is_deleted == False
        ).count()
        
        # Prepare skills data with gig_job_skill ID
        skills_data = []
        for skill in gig_job.skills:
            if not skill.is_deleted:
                # Get the gig_job_skill relationship ID
                gig_job_skill = self.db.query(GigJobSkill).filter(
                    GigJobSkill.gig_job_id == gig_job.id,
                    GigJobSkill.skill_id == skill.id
                ).first()
                
                skill_data = {
                    "id": skill.id,
                    "name": skill.name,
                    "created_at": skill.created_at,
                    "updated_at": skill.updated_at,
                    "is_deleted": skill.is_deleted
                }
                
                # Add gig_job_skill_id if relationship exists
                if gig_job_skill:
                    skill_data["gig_job_skill_id"] = gig_job_skill.id
                
                skills_data.append(skill_data)
        
        response_data = {
            "id": gig_job.id,
            "title": gig_job.title,
            "description": gig_job.description,
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
            "project_length": gig_job.project_length.value if hasattr(gig_job.project_length, 'value') else str(gig_job.project_length),
            "min_salary": gig_job.min_salary,
            "max_salary": gig_job.max_salary,
            "status": gig_job.status.value if hasattr(gig_job.status, 'value') else str(gig_job.status),
            "author": {
                "id": gig_job.author.id,
                "name": gig_job.author.name,
                "email": gig_job.author.email,
                "is_active": gig_job.author.is_active,
                "is_verified": gig_job.author.is_verified,
                "is_social_user": gig_job.author.is_social_user,
                "created_at": gig_job.author.created_at,
                "last_login": gig_job.author.last_login,
                "phone": gig_job.author.phone,
                "avatar_url": gig_job.author.avatar_url,
                "about_me": gig_job.author.about_me,
                "current_position": gig_job.author.current_position
            } if gig_job.author else None,
            "man_category": {
                "id": gig_job.category.id,
                "name": gig_job.category.name,
                "description": gig_job.category.description,
                "is_active": gig_job.category.is_active,
                "created_at": gig_job.category.created_at,
                "updated_at": gig_job.category.updated_at
            } if gig_job.category else None,
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

    def search_gig_jobs(self, search_term: str, pagination: PaginationParams) -> Tuple[List[dict], int]:
        """Search gig jobs by title, description, or skills"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(
            GigJob.is_deleted == False,
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
    
    def remove_gig_job_skill(self, gig_job_id: int, gig_job_skill_id: int, user_id: int) -> dict:
        """Remove GigJobSkill relationship from a gig job"""
        from ..models.gig_job import GigJob
        from ..models.gig_job_skill import GigJobSkill
        from ..models.skill import Skill
        
        # Get the gig job
        gig_job = self.db.query(GigJob).filter(
            GigJob.id == gig_job_id,
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        ).first()
        
        if not gig_job:
            raise ValueError("Gig job not found or you don't have permission to modify it")
        
        # Get the GigJobSkill relationship to remove
        gig_job_skill = self.db.query(GigJobSkill).filter(
            GigJobSkill.id == gig_job_skill_id,
            GigJobSkill.gig_job_id == gig_job_id
        ).first()
        
        if not gig_job_skill:
            raise ValueError("GigJobSkill relationship not found")
        
        # Get the skill name before removing
        skill = self.db.query(Skill).filter(Skill.id == gig_job_skill.skill_id).first()
        skill_name = skill.name if skill else "Unknown"
        
        # Remove the GigJobSkill relationship
        self.db.delete(gig_job_skill)
        
        self.db.commit()
        self.db.refresh(gig_job)
        
        # Load relationships for response
        gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.id == gig_job_id).first()
        
        return {
            "gig_job": self._prepare_gig_job_response(gig_job),
            "removed_skill": skill_name,
            "removed_gig_job_skill_id": gig_job_skill_id,
            "message": f"Successfully removed skill relationship: {skill_name}"
        }