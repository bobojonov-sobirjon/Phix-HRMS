from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models.job_post_type import JobPostType
from ..schemas.job_post_type import JobPostTypeCreate, JobPostTypeUpdate

class JobPostTypeRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, job_post_type: JobPostTypeCreate) -> JobPostType:
        db_job_post_type = JobPostType(**job_post_type.dict())
        self.db.add(db_job_post_type)
        self.db.commit()
        self.db.refresh(db_job_post_type)
        return db_job_post_type
    
    def get_all(self, skip: int = 0, limit: int = 100) -> list[JobPostType]:
        return self.db.query(JobPostType).filter(
            JobPostType.is_deleted == False
        ).offset(skip).limit(limit).all()
    
    def get_by_id(self, job_post_type_id: int) -> JobPostType:
        return self.db.query(JobPostType).filter(
            and_(
                JobPostType.id == job_post_type_id,
                JobPostType.is_deleted == False
            )
        ).first()
    
    def update(self, job_post_type_id: int, job_post_type: JobPostTypeUpdate) -> JobPostType:
        db_job_post_type = self.get_by_id(job_post_type_id)
        if not db_job_post_type:
            return None
        
        update_data = job_post_type.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job_post_type, field, value)
        
        self.db.commit()
        self.db.refresh(db_job_post_type)
        return db_job_post_type
    
    def delete(self, job_post_type_id: int) -> bool:
        db_job_post_type = self.get_by_id(job_post_type_id)
        if not db_job_post_type:
            return False
        
        db_job_post_type.is_deleted = True
        self.db.commit()
        return True 