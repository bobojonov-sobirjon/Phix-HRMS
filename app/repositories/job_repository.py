from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from ..models.job import Job
from ..models.job_skill import JobSkill
from ..models.skill import Skill
from ..schemas.job import JobCreate, JobUpdate

class JobRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, job: JobCreate) -> Job:
        db_job = Job(**job.dict(exclude={'skill_names'}))
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        
        # Handle skills
        if job.skill_names:
            for skill_name in job.skill_names:
                # Check if skill exists
                existing_skill = self.db.query(Skill).filter(
                    and_(
                        Skill.name == skill_name,
                        Skill.is_deleted == False
                    )
                ).first()
                
                if existing_skill:
                    skill_id = existing_skill.id
                else:
                    # Create new skill
                    new_skill = Skill(name=skill_name)
                    self.db.add(new_skill)
                    self.db.commit()
                    self.db.refresh(new_skill)
                    skill_id = new_skill.id
                
                # Create job_skill relationship
                job_skill = JobSkill(job_id=db_job.id, skill_id=skill_id)
                self.db.add(job_skill)
            
            self.db.commit()
            self.db.refresh(db_job)
        
        return db_job
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Job]:
        return self.db.query(Job).options(
            joinedload(Job.job_post_type),
            joinedload(Job.location)
        ).filter(
            Job.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Job]:
        return self.db.query(Job).options(
            joinedload(Job.job_post_type),
            joinedload(Job.location)
        ).filter(
            and_(
                Job.user_id == user_id,
                Job.is_deleted == False
            )
        ).offset(skip).limit(limit).all()
    
    def get_by_id(self, job_id: int) -> Optional[Job]:
        return self.db.query(Job).options(
            joinedload(Job.job_post_type),
            joinedload(Job.location)
        ).filter(
            and_(
                Job.id == job_id,
                Job.is_deleted == False
            )
        ).first()
    
    def update(self, job_id: int, job: JobUpdate) -> Optional[Job]:
        db_job = self.get_by_id(job_id)
        if not db_job:
            return None
        
        update_data = job.dict(exclude_unset=True, exclude={'skill_names'})
        for field, value in update_data.items():
            setattr(db_job, field, value)
        
        # Handle skills update if provided
        if job.skill_names is not None:
            # Remove existing job_skills
            self.db.query(JobSkill).filter(JobSkill.job_id == job_id).delete()
            
            # Add new skills
            for skill_name in job.skill_names:
                existing_skill = self.db.query(Skill).filter(
                    and_(
                        Skill.name == skill_name,
                        Skill.is_deleted == False
                    )
                ).first()
                
                if existing_skill:
                    skill_id = existing_skill.id
                else:
                    new_skill = Skill(name=skill_name)
                    self.db.add(new_skill)
                    self.db.commit()
                    self.db.refresh(new_skill)
                    skill_id = new_skill.id
                
                job_skill = JobSkill(job_id=job_id, skill_id=skill_id)
                self.db.add(job_skill)
        
        self.db.commit()
        self.db.refresh(db_job)
        return db_job
    
    def delete(self, job_id: int) -> bool:
        db_job = self.get_by_id(job_id)
        if not db_job:
            return False
        
        db_job.is_deleted = True
        self.db.commit()
        return True
    
    def filter_jobs(
        self,
        job_name: Optional[str] = None,
        location_ids: Optional[List[int]] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        experience_level: Optional[str] = None,
        work_mode: Optional[str] = None,
        job_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        query = self.db.query(Job).options(
            joinedload(Job.job_post_type),
            joinedload(Job.location)
        ).filter(Job.is_deleted == False)
        
        if job_name:
            query = query.filter(Job.title.ilike(f"%{job_name}%"))
        
        if location_ids:
            query = query.filter(Job.location_id.in_(location_ids))
        
        if price_min is not None:
            query = query.filter(Job.salary_min >= price_min)
        
        if price_max is not None:
            query = query.filter(Job.salary_max <= price_max)
        
        if experience_level:
            query = query.filter(Job.experience_level == experience_level)
        
        if work_mode:
            query = query.filter(Job.work_mode == work_mode)
        
        if job_type:
            query = query.filter(Job.job_type == job_type)
        
        return query.offset(skip).limit(limit).all() 