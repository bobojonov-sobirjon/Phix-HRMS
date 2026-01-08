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
from ..core.config import settings


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
        skill_ids = gig_job_data.skill_ids
        
        gig_job_dict = gig_job_data.model_dump(exclude={'skill_ids'})
        
        db_gig_job = GigJob(
            **gig_job_dict,
            author_id=author_id
        )
        self.db.add(db_gig_job)
        self.db.flush()
        
        if skill_ids:
            skills = self._get_skills_by_ids(skill_ids)
            unique_skills = list(dict.fromkeys(skills))
            db_gig_job.skills = unique_skills
        
        self.db.commit()
        self.db.refresh(db_gig_job)
        
        db_gig_job = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.id == db_gig_job.id).first()
        
        return self._prepare_gig_job_response(db_gig_job)

    def get_by_id(self, gig_job_id: int, current_user_id: Optional[int] = None) -> Optional[dict]:
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
        
        return self._prepare_gig_job_response(gig_job, current_user_id)

    def get_user_gig_jobs(self, user_id: int, pagination: PaginationParams, current_user_id: Optional[int] = None) -> Tuple[List[dict], int]:
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
        
        total = base_query.count()
        
        gig_jobs = base_query.offset(pagination.offset).limit(pagination.limit).all()
        
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job, current_user_id))
        
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
        sort_by: Optional[str] = "most_recent",
        current_user_id: Optional[int] = None
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
        
        if date_posted:
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(weeks=1))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        if sort_by == "most_recent":
            query = query.order_by(desc(GigJob.created_at))
        else:
            query = query.order_by(desc(GigJob.created_at))
        
        total = query.count()
        
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job, current_user_id))
        
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
        
        skill_ids = gig_job_data.skill_ids
        
        update_data = gig_job_data.model_dump(exclude_unset=True, exclude={'skill_ids'})
        
        gig_job.updated_at = func.now()
        
        for field, value in update_data.items():
            setattr(gig_job, field, value)
        
        if skill_ids is not None:
            new_skills = self._get_skills_by_ids(skill_ids)
            existing_skills = list(gig_job.skills)
            for new_skill in new_skills:
                if new_skill not in existing_skills:
                    existing_skills.append(new_skill)
            gig_job.skills = existing_skills
        
        self.db.commit()
        self.db.refresh(gig_job)
        
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
        sort_by: Optional[str] = "most_recent",
        current_user_id: Optional[int] = None
    ) -> Tuple[List[dict], int]:
        """Get all gig jobs with advanced filtering"""
        query = self.db.query(GigJob).options(
            joinedload(GigJob.category),
            joinedload(GigJob.subcategory),
            joinedload(GigJob.location),
            joinedload(GigJob.skills),
            joinedload(GigJob.author)
        ).filter(GigJob.is_deleted == False)
        
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
        
        if date_posted:
            now = datetime.utcnow()
            if date_posted == "past_24_hours":
                query = query.filter(GigJob.created_at >= now - timedelta(hours=24))
            elif date_posted == "past_week":
                query = query.filter(GigJob.created_at >= now - timedelta(weeks=1))
            elif date_posted == "past_month":
                query = query.filter(GigJob.created_at >= now - timedelta(days=30))
        
        if sort_by == "most_recent":
            query = query.order_by(desc(GigJob.created_at))
        else:
            query = query.order_by(desc(GigJob.created_at))
        
        total = query.count()
        
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job, current_user_id))
        
        return prepared_gig_jobs, total

    def _prepare_gig_job_response(self, gig_job: GigJob, current_user_id: Optional[int] = None) -> dict:
        """Prepare gig job response data"""
        proposal_count = self.db.query(Proposal).filter(
            Proposal.gig_job_id == gig_job.id,
            Proposal.is_deleted == False
        ).count()
        
        all_jobs_count = self.db.query(GigJob).filter(
            GigJob.author_id == gig_job.author_id,
            GigJob.is_deleted == False
        ).count()
        
        relevance_score = None
        is_saved = False
        is_send_proposal = False
        if current_user_id:
            relevance_score = self._calculate_relevance_score(gig_job, current_user_id)
            from ..models.saved_job import SavedJob
            is_saved = self.db.query(SavedJob).filter(
                SavedJob.user_id == current_user_id,
                SavedJob.gig_job_id == gig_job.id
            ).first() is not None
            is_send_proposal = self.db.query(Proposal).filter(
                Proposal.user_id == current_user_id,
                Proposal.gig_job_id == gig_job.id,
                Proposal.is_deleted == False
            ).first() is not None
        
        skills_data = []
        for skill in gig_job.skills:
            if not skill.is_deleted:
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
            "proposal_count": proposal_count,
            "all_jobs_count": all_jobs_count,
            "relevance_score": relevance_score,
            "is_saved": is_saved,
            "is_send_proposal": is_send_proposal
        }
        
        return response_data

    def _calculate_relevance_score(self, gig_job: GigJob, current_user_id: int) -> float:
        """Calculate relevance score based on user skills and job requirements"""
        from ..models.user_skill import UserSkill
        from ..models.user import User
        
        user_skills = self.db.query(UserSkill).filter(
            UserSkill.user_id == current_user_id,
            UserSkill.is_deleted == False
        ).all()
        
        if not user_skills:
            return 0.0
        
        user_skill_ids = {skill.skill_id for skill in user_skills}
        job_skill_ids = {skill.id for skill in gig_job.skills if not skill.is_deleted}
        
        if not job_skill_ids:
            return 0.0
        
        matching_skills = user_skill_ids.intersection(job_skill_ids)
        skill_match_percentage = (len(matching_skills) / len(job_skill_ids)) * 100
        
        user = self.db.query(User).filter(User.id == current_user_id).first()
        if not user:
            return round(skill_match_percentage, 2)
        
        bonus_score = 0.0
        
        if hasattr(gig_job, 'experience_level') and hasattr(user, 'experience_level'):
            if gig_job.experience_level == user.experience_level:
                bonus_score += 10.0
        
        if hasattr(gig_job, 'location_id') and gig_job.location_id and hasattr(user, 'location_id'):
            if gig_job.location_id == user.location_id:
                bonus_score += 5.0
        
        if hasattr(user, 'expected_salary') and user.expected_salary:
            if gig_job.min_salary <= user.expected_salary <= gig_job.max_salary:
                bonus_score += 15.0
            elif user.expected_salary < gig_job.min_salary:
                bonus_score += 5.0
        
        final_score = min(skill_match_percentage + bonus_score, 100.0)
        
        return round(final_score, 2)

    def search_gig_jobs(self, search_term: str, pagination: PaginationParams, current_user_id: Optional[int] = None) -> Tuple[List[dict], int]:
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
        
        total = query.count()
        
        gig_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        prepared_gig_jobs = []
        for gig_job in gig_jobs:
            prepared_gig_jobs.append(self._prepare_gig_job_response(gig_job, current_user_id))
        
        return prepared_gig_jobs, total
    
    def remove_gig_job_skill(self, gig_job_id: int, gig_job_skill_id: int, user_id: int) -> dict:
        """Remove GigJobSkill relationship from a gig job"""
        from ..models.gig_job import GigJob
        from ..models.gig_job_skill import GigJobSkill
        from ..models.skill import Skill
        
        gig_job = self.db.query(GigJob).filter(
            GigJob.id == gig_job_id,
            GigJob.author_id == user_id,
            GigJob.is_deleted == False
        ).first()
        
        if not gig_job:
            raise ValueError("Gig job not found or you don't have permission to modify it")
        
        gig_job_skill = self.db.query(GigJobSkill).filter(
            GigJobSkill.id == gig_job_skill_id,
            GigJobSkill.gig_job_id == gig_job_id
        ).first()
        
        if not gig_job_skill:
            raise ValueError("GigJobSkill relationship not found")
        
        skill = self.db.query(Skill).filter(Skill.id == gig_job_skill.skill_id).first()
        skill_name = skill.name if skill else "Unknown"
        
        self.db.delete(gig_job_skill)
        
        self.db.commit()
        self.db.refresh(gig_job)
        
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