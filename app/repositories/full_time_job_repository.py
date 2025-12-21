from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.full_time_job import FullTimeJob
from ..models.corporate_profile import CorporateProfile
from ..models.skill import Skill
from ..schemas.full_time_job import FullTimeJobCreate, FullTimeJobUpdate
from ..core.config import settings


class FullTimeJobRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def _get_skills_by_ids(self, skill_ids: List[int]) -> List[Skill]:
        """Get existing skills by their IDs"""
        if not skill_ids:
            return []
        
        skills = self.db.query(Skill).filter(
            Skill.id.in_(skill_ids),
            Skill.is_deleted == False
        ).all()
        
        return skills
    
    
    def _prepare_full_time_job_response(self, job: FullTimeJob, current_user_id: Optional[int] = None) -> dict:
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
        
        # Count all jobs by the user who created this job
        all_jobs_count = self.db.query(FullTimeJob).filter(
            FullTimeJob.created_by_user_id == job.created_by_user_id
        ).count()
        
        # Count followers for the company
        company_followers_count = 0
        company_follow_relation_id = None
        if job.company_id:
            from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
            follow_repo = CorporateProfileFollowRepository(self.db)
            company_followers_count = follow_repo.count_followers(job.company_id)
            
            # Check if current user is following this company
            if current_user_id:
                follow_relation = follow_repo.get_by_user_and_profile(current_user_id, job.company_id)
                if follow_relation:
                    company_follow_relation_id = follow_relation.id
        
        # Calculate relevance score if current user is provided
        relevance_score = None
        is_saved = False
        is_send_proposal = False
        if current_user_id:
            relevance_score = self._calculate_relevance_score(job, current_user_id)
            # Check if job is saved by current user
            from ..models.saved_job import SavedJob
            is_saved = self.db.query(SavedJob).filter(
                SavedJob.user_id == current_user_id,
                SavedJob.full_time_job_id == job.id
            ).first() is not None
            # Check if user has sent a proposal for this job
            from ..models.proposal import Proposal
            is_send_proposal = self.db.query(Proposal).filter(
                Proposal.user_id == current_user_id,
                Proposal.full_time_job_id == job.id,
                Proposal.is_deleted == False
            ).first() is not None
        
        # Prepare company logo URL with base URL
        company_logo_url = None
        if job.company and job.company.logo_url:
            logo_url = job.company.logo_url
            if logo_url and not logo_url.startswith('http'):
                company_logo_url = f"{settings.BASE_URL}{logo_url}"
            else:
                company_logo_url = logo_url
        
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
            "pay_period": job.pay_period.value if job.pay_period else "PER_MONTH",
            "status": job.status,
            "company_id": job.company_id,
            "company_name": job.company.company.name if job.company and job.company.company else "",
            "company_logo_url": company_logo_url,
            "category_id": job.category_id,
            "category_name": job.category.name if job.category else "",
            "subcategory_id": job.subcategory_id,
            "subcategory_name": job.subcategory.name if job.subcategory else None,
            "created_by_user_id": job.created_by_user_id,
            "created_by_user_name": job.created_by_user.name if job.created_by_user else "",
            "created_by_role": job.created_by_role.value if job.created_by_role else "",
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "skills": skills_data,
            "all_jobs_count": all_jobs_count,
            "relevance_score": relevance_score,
            "is_saved": is_saved,
            "is_send_proposal": is_send_proposal,
            "company_followers_count": company_followers_count,
            "company_follow_relation_id": company_follow_relation_id
        }
        
        return response_data

    def _calculate_relevance_score(self, job: FullTimeJob, current_user_id: int) -> float:
        """Calculate relevance score based on user skills and job requirements"""
        from ..models.user_skill import UserSkill
        from ..models.user import User
        
        # Get user's skills
        user_skills = self.db.query(UserSkill).filter(
            UserSkill.user_id == current_user_id,
            UserSkill.is_deleted == False
        ).all()
        
        if not user_skills:
            return 0.0
        
        user_skill_ids = {skill.skill_id for skill in user_skills}
        job_skill_ids = {skill.id for skill in job.skills if not skill.is_deleted}
        
        if not job_skill_ids:
            return 0.0
        
        # Calculate skill match percentage (primary factor)
        matching_skills = user_skill_ids.intersection(job_skill_ids)
        skill_match_percentage = (len(matching_skills) / len(job_skill_ids)) * 100
        
        # Get user details for additional factors
        user = self.db.query(User).filter(User.id == current_user_id).first()
        if not user:
            return round(skill_match_percentage, 2)
        
        # Additional relevance factors
        bonus_score = 0.0
        
        # Experience level match bonus
        if hasattr(job, 'experience_level') and hasattr(user, 'experience_level'):
            if job.experience_level == user.experience_level:
                bonus_score += 10.0
        
        # Work mode match bonus
        if hasattr(job, 'work_mode') and hasattr(user, 'preferred_work_mode'):
            if job.work_mode == user.preferred_work_mode:
                bonus_score += 8.0
        
        # Location match bonus (if user has location preference)
        if hasattr(job, 'location') and job.location and hasattr(user, 'location_id'):
            if job.location == user.location_id:
                bonus_score += 5.0
        
        # Salary range match bonus (if user's expected salary is within job range)
        if hasattr(user, 'expected_salary') and user.expected_salary:
            if job.min_salary <= user.expected_salary <= job.max_salary:
                bonus_score += 15.0
            elif user.expected_salary < job.min_salary:
                # User expects less than minimum, but still relevant
                bonus_score += 5.0
        
        # Job type match bonus
        if hasattr(job, 'job_type') and hasattr(user, 'preferred_job_type'):
            if job.job_type == user.preferred_job_type:
                bonus_score += 7.0
        
        # Calculate final score (skill match + bonuses, capped at 100)
        final_score = min(skill_match_percentage + bonus_score, 100.0)
        
        return round(final_score, 2)

    def _format_job_response(self, job: FullTimeJob) -> dict:
        """Format job response with all related data including context"""
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
        
        # Prepare company logo URL with base URL
        company_logo_url = None
        if job.company and job.company.logo_url:
            logo_url = job.company.logo_url
            if logo_url and not logo_url.startswith('http'):
                company_logo_url = f"{settings.BASE_URL}{logo_url}"
            else:
                company_logo_url = logo_url
        
        # Create response data
        response_data = {
            "id": job.id,
            "title": job.title,
            "description": job.description,
            "responsibilities": job.responsibilities,
            "location": job.location,
            "job_type": job.job_type.value,
            "work_mode": job.work_mode.value,
            "experience_level": job.experience_level.value,
            "min_salary": job.min_salary,
            "max_salary": job.max_salary,
            "pay_period": job.pay_period.value if job.pay_period else "PER_MONTH",
            "status": job.status.value,
            "company_id": job.company_id,
            "company_name": job.company.company.name if job.company and job.company.company else "",
            "company_logo_url": company_logo_url,
            "category_id": job.category_id,
            "category_name": job.category.name if job.category else "",
            "subcategory_id": job.subcategory_id,
            "subcategory_name": job.subcategory.name if job.subcategory else None,
            "created_by_user_id": job.created_by_user_id,
            "created_by_user_name": job.created_by_user.name if job.created_by_user else "",
            "created_by_role": job.created_by_role.value,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "skills": skills_data
        }
        
        return response_data
    
    def create(self, full_time_job: FullTimeJobCreate, company_id: int) -> dict:
        """Create a new full-time job with skills"""
        # Extract skill_ids from the request
        skill_ids = full_time_job.skill_ids
        job_dict = full_time_job.model_dump(exclude={'skill_ids'})
        
        # Create the job
        db_job = FullTimeJob(
            **job_dict,
            company_id=company_id
        )
        self.db.add(db_job)
        self.db.flush()  # Flush to get the ID
        
        # Get skills by IDs and add them to the job
        if skill_ids:
            skills = self._get_skills_by_ids(skill_ids)
            db_job.skills = skills
        
        self.db.commit()
        self.db.refresh(db_job)
        
        # Load company relationship for response
        db_job.company = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == company_id
        ).first()
        
        # Return prepared response data
        return self._prepare_full_time_job_response(db_job)

    def create_with_context(self, job_data, corporate_profile_id, created_by_user_id, created_by_role):
        """Create job with context about who created it"""
        from ..models.team_member import TeamMemberRole
        
        # Extract skill_ids from the request
        skill_ids = job_data.skill_ids if hasattr(job_data, 'skill_ids') else []
        
        job_dict = job_data.dict() if hasattr(job_data, 'dict') else job_data.model_dump()
        
        # Remove fields that are not part of FullTimeJob model
        job_dict.pop('skill_ids', None)
        job_dict.pop('corporate_profile_id', None)
        
        # Add context fields
        job_dict.update({
            "company_id": corporate_profile_id,
            "created_by_user_id": created_by_user_id,
            "created_by_role": created_by_role
        })
        
        # Create the job
        db_job = FullTimeJob(**job_dict)
        self.db.add(db_job)
        self.db.flush()  # Flush to get the ID
        
        # Get skills by IDs and add them to the job
        if skill_ids:
            skills = self._get_skills_by_ids(skill_ids)
            db_job.skills = skills
        
        self.db.commit()
        self.db.refresh(db_job)
        
        # Manually build response to avoid attribute errors
        # Convert skills to dict format
        skills_data = []
        for skill in db_job.skills:
            skills_data.append({
                "id": skill.id,
                "name": skill.name,
                "created_at": skill.created_at,
                "updated_at": skill.updated_at,
                "is_deleted": skill.is_deleted
            })
        
        # Load related objects
        from ..models.category import Category
        from ..models.user import User
        
        company = self.db.query(CorporateProfile).filter(
            CorporateProfile.id == corporate_profile_id
        ).first()
        
        category = self.db.query(Category).filter(
            Category.id == db_job.category_id
        ).first()
        
        subcategory = None
        if db_job.subcategory_id:
            subcategory = self.db.query(Category).filter(
                Category.id == db_job.subcategory_id
            ).first()
        
        created_by_user = self.db.query(User).filter(
            User.id == created_by_user_id
        ).first()
        
        # Count followers for the company
        company_followers_count = 0
        company_follow_relation_id = None
        if corporate_profile_id:
            from ..repositories.corporate_profile_follow_repository import CorporateProfileFollowRepository
            follow_repo = CorporateProfileFollowRepository(self.db)
            company_followers_count = follow_repo.count_followers(corporate_profile_id)
            # Note: In create_with_context, we don't have current_user_id, so follow_relation_id will be None
        
        # Prepare company logo URL with base URL
        company_logo_url = None
        if company and company.logo_url:
            logo_url = company.logo_url
            if logo_url and not logo_url.startswith('http'):
                company_logo_url = f"{settings.BASE_URL}{logo_url}"
            else:
                company_logo_url = logo_url
        
        # Create response data manually
        response_data = {
            "id": db_job.id,
            "title": db_job.title,
            "description": db_job.description,
            "responsibilities": db_job.responsibilities,
            "location": db_job.location,
            "job_type": db_job.job_type.value,
            "work_mode": db_job.work_mode.value,
            "experience_level": db_job.experience_level.value,
            "min_salary": db_job.min_salary,
            "max_salary": db_job.max_salary,
            "status": db_job.status.value,
            "company_id": corporate_profile_id,
            "company_name": company.company.name if company and company.company else "",
            "company_logo_url": company_logo_url,
            "category_id": db_job.category_id,
            "category_name": category.name if category else "",
            "subcategory_id": db_job.subcategory_id,
            "subcategory_name": subcategory.name if subcategory else None,
            "created_by_user_id": created_by_user_id,
            "created_by_user_name": created_by_user.name if created_by_user else "",
            "created_by_role": created_by_role.value if hasattr(created_by_role, 'value') else str(created_by_role),
            "created_at": db_job.created_at,
            "updated_at": db_job.updated_at,
            "skills": skills_data,
            "all_jobs_count": 0,
            "relevance_score": None,
            "is_saved": False,
            "is_send_proposal": False,
            "company_followers_count": company_followers_count,
            "company_follow_relation_id": company_follow_relation_id
        }
        
        return response_data
    
    def get_by_id(self, job_id: int, current_user_id: Optional[int] = None) -> Optional[dict]:
        """Get full-time job by ID with skills"""
        job = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(
            FullTimeJob.id == job_id
        ).first()
        
        if job:
            return self._prepare_full_time_job_response(job, current_user_id)
        return None

    def get_object_by_id(self, job_id: int) -> Optional[FullTimeJob]:
        """Get full-time job object by ID (for internal use)"""
        return self.db.query(FullTimeJob).filter(FullTimeJob.id == job_id).first()
    
    def get_by_company_id(self, company_id: int, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None, status: Optional[str] = None) -> List[dict]:
        """Get all jobs by company ID, ordered by created_at DESC (recently posted first)"""
        from sqlalchemy import desc
        from ..models.full_time_job import JobStatus
        
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).filter(
            FullTimeJob.company_id == company_id
        )
        
        # Filter by status if provided
        if status:
            query = query.filter(FullTimeJob.status == JobStatus[status.upper()])
        
        jobs = query.order_by(desc(FullTimeJob.created_at)).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None) -> List[dict]:
        """Get all jobs by user ID (through corporate profile) - OWNER only"""
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
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def get_user_created_jobs(self, user_id: int, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None) -> List[dict]:
        """Get all jobs created by user (as owner or team member)"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company),
            joinedload(FullTimeJob.category),
            joinedload(FullTimeJob.subcategory),
            joinedload(FullTimeJob.created_by_user)
        ).filter(
            FullTimeJob.created_by_user_id == user_id
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def get_user_accessible_jobs(self, user_id: int, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None) -> List[dict]:
        """Get all jobs user can access (as owner or team member)"""
        from app.models.team_member import TeamMember, TeamMemberStatus
        
        # Get corporate profiles where user is owner or team member
        owned_profiles = self.db.query(CorporateProfile).filter(
            CorporateProfile.user_id == user_id
        ).all()
        
        team_memberships = self.db.query(TeamMember).filter(
            TeamMember.user_id == user_id,
            TeamMember.status == TeamMemberStatus.ACCEPTED
        ).all()
        
        # Collect all corporate profile IDs
        corporate_profile_ids = [profile.id for profile in owned_profiles]
        corporate_profile_ids.extend([membership.corporate_profile_id for membership in team_memberships])
        
        if not corporate_profile_ids:
            return []
        
        # Get all jobs from these corporate profiles
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company),
            joinedload(FullTimeJob.category),
            joinedload(FullTimeJob.subcategory),
            joinedload(FullTimeJob.created_by_user)
        ).filter(
            FullTimeJob.company_id.in_(corporate_profile_ids)
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def get_all_active(self, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None, category_id: Optional[int] = None, subcategory_id: Optional[int] = None) -> List[dict]:
        """Get all active full-time jobs from verified corporate profiles"""
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).join(CorporateProfile, FullTimeJob.company_id == CorporateProfile.id).filter(
            and_(
                FullTimeJob.status == "ACTIVE",
                CorporateProfile.is_verified == True,
                CorporateProfile.is_deleted == False
            )
        )
        
        if category_id:
            query = query.filter(FullTimeJob.category_id == category_id)
        
        if subcategory_id:
            query = query.filter(FullTimeJob.subcategory_id == subcategory_id)
        
        jobs = query.offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def get_all(self, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None) -> List[dict]:
        """Get all full-time jobs with pagination"""
        jobs = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def update(self, job_id: int, full_time_job: FullTimeJobUpdate) -> Optional[dict]:
        """Update full-time job with skills"""
        db_job = self.db.query(FullTimeJob).filter(FullTimeJob.id == job_id).first()
        if not db_job:
            return None
        
        update_data = full_time_job.model_dump(exclude_unset=True)
        
        # Handle skills separately
        skill_ids = update_data.pop('skill_ids', None)
        
        # Update other fields
        for field, value in update_data.items():
            setattr(db_job, field, value)
        
        # Update skills if provided
        if skill_ids is not None:
            skills = self._get_skills_by_ids(skill_ids)
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
        db_job = self.get_object_by_id(job_id)
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
                   skill_ids: Optional[List[int]] = None,
                   category_id: Optional[int] = None,
                   subcategory_id: Optional[int] = None,
                   min_salary: Optional[float] = None,
                   max_salary: Optional[float] = None,
                   skip: int = 0,
                   limit: int = 100,
                   current_user_id: Optional[int] = None) -> List[dict]:
        """Search jobs with filters including skill IDs - only from verified corporate profiles"""
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company)
        ).join(CorporateProfile, FullTimeJob.company_id == CorporateProfile.id).filter(
            and_(
                FullTimeJob.status == "ACTIVE",
                CorporateProfile.is_verified == True,
                CorporateProfile.is_deleted == False
            )
        )
        
        if title:
            query = query.filter(FullTimeJob.title.ilike(f"%{title}%"))
        
        if location:
            query = query.filter(FullTimeJob.location.ilike(f"%{location}%"))
        
        if experience_level:
            query = query.filter(FullTimeJob.experience_level == experience_level)
        
        if work_mode:
            query = query.filter(FullTimeJob.work_mode == work_mode)
        
        if category_id:
            query = query.filter(FullTimeJob.category_id == category_id)
        
        if subcategory_id:
            query = query.filter(FullTimeJob.subcategory_id == subcategory_id)
        
        if skill_ids:
            # Filter jobs that have any of the specified skills
            query = query.join(FullTimeJob.skills).filter(
                Skill.id.in_(skill_ids)
            ).distinct()
        
        if min_salary is not None:
            query = query.filter(FullTimeJob.max_salary >= min_salary)
        
        if max_salary is not None:
            query = query.filter(FullTimeJob.min_salary <= max_salary)
        
        jobs = query.offset(skip).limit(limit).all()
        
        # Prepare response data for each job
        prepared_jobs = []
        for job in jobs:
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def count_total(self) -> int:
        """Get total count of full-time jobs"""
        return self.db.query(FullTimeJob).count()
    
    def count_active(self) -> int:
        """Get count of active full-time jobs from verified corporate profiles"""
        return self.db.query(FullTimeJob).join(CorporateProfile, FullTimeJob.company_id == CorporateProfile.id).filter(
            and_(
                FullTimeJob.status == "ACTIVE",
                CorporateProfile.is_verified == True,
                CorporateProfile.is_deleted == False
            )
        ).count()
    
    def count_by_company(self, company_id: int) -> int:
        """Get count of jobs by company"""
        return self.db.query(FullTimeJob).filter(
            FullTimeJob.company_id == company_id
        ).count()
    
    def count_by_user(self, user_id: int) -> int:
        """Get count of jobs by user (owner only)"""
        return self.db.query(FullTimeJob).join(
            CorporateProfile, FullTimeJob.company_id == CorporateProfile.id
        ).filter(
            CorporateProfile.user_id == user_id
        ).count()
    
    def count_user_created_jobs(self, user_id: int) -> int:
        """Get count of jobs created by user (as owner or team member)"""
        return self.db.query(FullTimeJob).filter(
            FullTimeJob.created_by_user_id == user_id
        ).count()
    
    def count_user_accessible_jobs(self, user_id: int) -> int:
        """Get count of jobs user can access (as owner or team member)"""
        from app.models.team_member import TeamMember, TeamMemberStatus
        
        # Get corporate profiles where user is owner or team member
        owned_profiles = self.db.query(CorporateProfile).filter(
            CorporateProfile.user_id == user_id
        ).all()
        
        team_memberships = self.db.query(TeamMember).filter(
            TeamMember.user_id == user_id,
            TeamMember.status == TeamMemberStatus.ACCEPTED
        ).all()
        
        # Collect all corporate profile IDs
        corporate_profile_ids = [profile.id for profile in owned_profiles]
        corporate_profile_ids.extend([membership.corporate_profile_id for membership in team_memberships])
        
        if not corporate_profile_ids:
            return 0
        
        return self.db.query(FullTimeJob).filter(
            FullTimeJob.company_id.in_(corporate_profile_ids)
        ).count()
    
    def get_by_corporate_profiles_with_filters(self, 
                                             corporate_profile_ids: List[int],
                                             skip: int = 0,
                                             limit: int = 100,
                                             status: Optional[str] = None,
                                             job_type: Optional[str] = None,
                                             experience_level: Optional[str] = None,
                                             work_mode: Optional[str] = None,
                                             location: Optional[str] = None,
                                             min_salary: Optional[float] = None,
                                             max_salary: Optional[float] = None,
                                             current_user_id: Optional[int] = None) -> List[dict]:
        """Get jobs by corporate profile IDs with filters"""
        query = self.db.query(FullTimeJob).options(
            joinedload(FullTimeJob.skills),
            joinedload(FullTimeJob.company),
            joinedload(FullTimeJob.category),
            joinedload(FullTimeJob.subcategory),
            joinedload(FullTimeJob.created_by_user)
        ).filter(
            FullTimeJob.company_id.in_(corporate_profile_ids)
        )
        
        # Apply filters
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
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
        return prepared_jobs
    
    def count_by_corporate_profiles_with_filters(self, 
                                               corporate_profile_ids: List[int],
                                               status: Optional[str] = None,
                                               job_type: Optional[str] = None,
                                               experience_level: Optional[str] = None,
                                               work_mode: Optional[str] = None,
                                               location: Optional[str] = None,
                                               min_salary: Optional[float] = None,
                                               max_salary: Optional[float] = None) -> int:
        """Get count of jobs by corporate profile IDs with filters"""
        query = self.db.query(FullTimeJob).filter(
            FullTimeJob.company_id.in_(corporate_profile_ids)
        )
        
        # Apply filters
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
                                   max_salary: Optional[float] = None,
                                   current_user_id: Optional[int] = None) -> List[dict]:
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
            prepared_jobs.append(self._prepare_full_time_job_response(job, current_user_id))
        
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
