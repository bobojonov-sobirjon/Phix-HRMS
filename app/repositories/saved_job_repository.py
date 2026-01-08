from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.saved_job import SavedJob
from app.models.gig_job import GigJob
from app.models.full_time_job import FullTimeJob
from app.models.user import User
from app.schemas.saved_job import SavedJobCreate
from app.pagination import PaginationParams


class SavedJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, saved_job_data: SavedJobCreate, user_id: int) -> SavedJob:
        """Create a new saved job"""
        if not saved_job_data.gig_job_id and not saved_job_data.full_time_job_id:
            raise ValueError("Either gig_job_id or full_time_job_id must be provided")
        
        if saved_job_data.gig_job_id and saved_job_data.full_time_job_id:
            raise ValueError("Cannot save both gig_job_id and full_time_job_id in the same record")

        existing = self.get_by_user_and_job(
            user_id=user_id,
            gig_job_id=saved_job_data.gig_job_id,
            full_time_job_id=saved_job_data.full_time_job_id
        )
        if existing:
            raise ValueError("Job is already saved")

        db_saved_job = SavedJob(
            **saved_job_data.model_dump(),
            user_id=user_id
        )
        self.db.add(db_saved_job)
        self.db.commit()
        self.db.refresh(db_saved_job)
        return db_saved_job

    def get_by_id(self, saved_job_id: int) -> Optional[SavedJob]:
        """Get saved job by ID with relationships"""
        return self.db.query(SavedJob).options(
            joinedload(SavedJob.user).joinedload(User.location),
            joinedload(SavedJob.user).joinedload(User.main_category),
            joinedload(SavedJob.user).joinedload(User.sub_category),
            joinedload(SavedJob.user).joinedload(User.skills),
            joinedload(SavedJob.gig_job).joinedload(GigJob.category),
            joinedload(SavedJob.gig_job).joinedload(GigJob.subcategory),
            joinedload(SavedJob.gig_job).joinedload(GigJob.location),
            joinedload(SavedJob.gig_job).joinedload(GigJob.skills),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.category),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(SavedJob.id == saved_job_id).first()

    def get_by_user_and_job(
        self, 
        user_id: int, 
        gig_job_id: Optional[int] = None, 
        full_time_job_id: Optional[int] = None
    ) -> Optional[SavedJob]:
        """Get saved job by user and job IDs"""
        query = self.db.query(SavedJob).filter(SavedJob.user_id == user_id)
        
        if gig_job_id:
            query = query.filter(SavedJob.gig_job_id == gig_job_id)
        if full_time_job_id:
            query = query.filter(SavedJob.full_time_job_id == full_time_job_id)
            
        return query.first()

    def get_user_saved_jobs(self, user_id: int, pagination: PaginationParams) -> tuple[List[SavedJob], int]:
        """Get paginated saved jobs for a specific user with relationships"""
        query = self.db.query(SavedJob).options(
            joinedload(SavedJob.user).joinedload(User.location),
            joinedload(SavedJob.user).joinedload(User.main_category),
            joinedload(SavedJob.user).joinedload(User.sub_category),
            joinedload(SavedJob.user).joinedload(User.skills),
            joinedload(SavedJob.gig_job).joinedload(GigJob.category),
            joinedload(SavedJob.gig_job).joinedload(GigJob.subcategory),
            joinedload(SavedJob.gig_job).joinedload(GigJob.location),
            joinedload(SavedJob.gig_job).joinedload(GigJob.skills),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.category),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(SavedJob.user_id == user_id)
        
        total = query.count()
        
        saved_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return saved_jobs, total

    def get_user_saved_gig_jobs(self, user_id: int, pagination: PaginationParams) -> tuple[List[SavedJob], int]:
        """Get paginated saved gig jobs for a specific user with relationships"""
        query = self.db.query(SavedJob).options(
            joinedload(SavedJob.user).joinedload(User.location),
            joinedload(SavedJob.user).joinedload(User.main_category),
            joinedload(SavedJob.user).joinedload(User.sub_category),
            joinedload(SavedJob.user).joinedload(User.skills),
            joinedload(SavedJob.gig_job).joinedload(GigJob.category),
            joinedload(SavedJob.gig_job).joinedload(GigJob.subcategory),
            joinedload(SavedJob.gig_job).joinedload(GigJob.location),
            joinedload(SavedJob.gig_job).joinedload(GigJob.skills)
        ).filter(
            and_(SavedJob.user_id == user_id, SavedJob.gig_job_id.isnot(None))
        )
        
        total = query.count()
        
        saved_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return saved_jobs, total

    def get_user_saved_full_time_jobs(self, user_id: int, pagination: PaginationParams) -> tuple[List[SavedJob], int]:
        """Get paginated saved full-time jobs for a specific user with relationships"""
        query = self.db.query(SavedJob).options(
            joinedload(SavedJob.user).joinedload(User.location),
            joinedload(SavedJob.user).joinedload(User.main_category),
            joinedload(SavedJob.user).joinedload(User.sub_category),
            joinedload(SavedJob.user).joinedload(User.skills),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.category),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(SavedJob.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(
            and_(SavedJob.user_id == user_id, SavedJob.full_time_job_id.isnot(None))
        )
        
        total = query.count()
        
        saved_jobs = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return saved_jobs, total

    def delete(self, saved_job_id: int, user_id: int) -> bool:
        """Delete saved job (only by owner)"""
        saved_job = self.db.query(SavedJob).filter(
            and_(SavedJob.id == saved_job_id, SavedJob.user_id == user_id)
        ).first()
        
        if not saved_job:
            return False
        
        self.db.delete(saved_job)
        self.db.commit()
        return True

    def delete_by_job(self, user_id: int, gig_job_id: Optional[int] = None, full_time_job_id: Optional[int] = None) -> bool:
        """Delete saved job by job IDs (only by owner)"""
        query = self.db.query(SavedJob).filter(SavedJob.user_id == user_id)
        
        if gig_job_id:
            query = query.filter(SavedJob.gig_job_id == gig_job_id)
        if full_time_job_id:
            query = query.filter(SavedJob.full_time_job_id == full_time_job_id)
            
        saved_job = query.first()
        
        if not saved_job:
            return False
        
        self.db.delete(saved_job)
        self.db.commit()
        return True

    def is_job_saved(self, user_id: int, gig_job_id: Optional[int] = None, full_time_job_id: Optional[int] = None) -> bool:
        """Check if a job is saved by the user"""
        query = self.db.query(SavedJob).filter(SavedJob.user_id == user_id)
        
        if gig_job_id:
            query = query.filter(SavedJob.gig_job_id == gig_job_id)
        if full_time_job_id:
            query = query.filter(SavedJob.full_time_job_id == full_time_job_id)
            
        return query.first() is not None
