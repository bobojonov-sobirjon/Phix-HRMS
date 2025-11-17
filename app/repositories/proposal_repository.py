from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from app.models.proposal import Proposal
from app.models.gig_job import GigJob
from app.models.full_time_job import FullTimeJob
from app.models.user import User
from app.schemas.proposal import ProposalCreate, ProposalUpdate
from app.pagination import PaginationParams


class ProposalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, proposal_data: ProposalCreate, user_id: int) -> Proposal:
        """Create a new proposal"""
        db_proposal = Proposal(
            **proposal_data.model_dump(),
            user_id=user_id
        )
        self.db.add(db_proposal)
        self.db.commit()
        self.db.refresh(db_proposal)
        return db_proposal

    def get_by_id(self, proposal_id: int) -> Optional[Proposal]:
        """Get proposal by ID with relationships"""
        return self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Proposal.gig_job).joinedload(GigJob.skills),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(Proposal.id == proposal_id).first()

    def get_user_proposals(self, user_id: int, pagination: PaginationParams) -> tuple[List[Proposal], int]:
        """Get paginated proposals submitted by a specific user with relationships"""
        query = self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Proposal.gig_job).joinedload(GigJob.skills),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(Proposal.user_id == user_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        proposals = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return proposals, total

    def get_user_gig_job_proposals(self, user_id: int, pagination: PaginationParams) -> tuple[List[Proposal], int]:
        """Get paginated gig job proposals submitted by a specific user with relationships"""
        query = self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Proposal.gig_job).joinedload(GigJob.skills)
        ).filter(
            and_(Proposal.user_id == user_id, Proposal.gig_job_id.isnot(None))
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        proposals = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return proposals, total

    def get_user_full_time_job_proposals(self, user_id: int, pagination: PaginationParams) -> tuple[List[Proposal], int]:
        """Get paginated full-time job proposals submitted by a specific user with relationships"""
        query = self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(
            and_(Proposal.user_id == user_id, Proposal.full_time_job_id.isnot(None))
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        proposals = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return proposals, total

    def get_gig_job_proposals(self, gig_job_id: int, pagination: PaginationParams) -> tuple[List[Proposal], int]:
        """Get paginated proposals for a specific gig job with relationships"""
        query = self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Proposal.gig_job).joinedload(GigJob.skills),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(Proposal.gig_job_id == gig_job_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        proposals = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return proposals, total

    def get_full_time_job_proposals(self, full_time_job_id: int, pagination: PaginationParams) -> tuple[List[Proposal], int]:
        """Get paginated proposals for a specific full-time job with relationships"""
        query = self.db.query(Proposal).options(
            joinedload(Proposal.user).joinedload(User.location),
            joinedload(Proposal.user).joinedload(User.main_category),
            joinedload(Proposal.user).joinedload(User.sub_category),
            joinedload(Proposal.user).joinedload(User.skills),
            joinedload(Proposal.gig_job).joinedload(GigJob.category),
            joinedload(Proposal.gig_job).joinedload(GigJob.subcategory),
            joinedload(Proposal.gig_job).joinedload(GigJob.location),
            joinedload(Proposal.gig_job).joinedload(GigJob.skills),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.category),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.subcategory),
            joinedload(Proposal.full_time_job).joinedload(FullTimeJob.skills)
        ).filter(Proposal.full_time_job_id == full_time_job_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        proposals = query.offset(pagination.offset).limit(pagination.limit).all()
        
        return proposals, total

    def update(self, proposal_id: int, proposal_data: ProposalUpdate, user_id: int) -> Optional[Proposal]:
        """Update proposal (only by author)"""
        proposal = self.db.query(Proposal).filter(
            and_(Proposal.id == proposal_id, Proposal.user_id == user_id)
        ).first()
        
        if not proposal:
            return None
        
        update_data = proposal_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(proposal, field, value)
        
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def delete(self, proposal_id: int, user_id: int) -> bool:
        """Delete proposal (only by author)"""
        proposal = self.db.query(Proposal).filter(
            and_(Proposal.id == proposal_id, Proposal.user_id == user_id)
        ).first()
        
        if not proposal:
            return False
        
        self.db.delete(proposal)
        self.db.commit()
        return True

    def check_user_proposal_exists(self, user_id: int, job_id: int, job_type: str = "gig") -> bool:
        """Check if user has already submitted a proposal for a specific job"""
        if job_type == "gig":
            return self.db.query(Proposal).filter(
                and_(Proposal.user_id == user_id, Proposal.gig_job_id == job_id)
            ).first() is not None
        elif job_type == "full_time":
            return self.db.query(Proposal).filter(
                and_(Proposal.user_id == user_id, Proposal.full_time_job_id == job_id)
            ).first() is not None
        return False

    def mark_as_read(self, proposal_id: int) -> Optional[Proposal]:
        """Mark proposal as read"""
        proposal = self.db.query(Proposal).filter(Proposal.id == proposal_id).first()
        
        if not proposal:
            return None
        
        if not proposal.is_read:
            proposal.is_read = True
            self.db.commit()
            self.db.refresh(proposal)
        
        return proposal

    def get_by_file_path(self, file_path: str) -> Optional[Proposal]:
        """Get proposal by file path in attachments"""
        import json
        proposals = self.db.query(Proposal).filter(Proposal.attachments.isnot(None)).all()
        
        for proposal in proposals:
            if proposal.attachments:
                try:
                    file_paths = json.loads(proposal.attachments)
                    if file_path in file_paths:
                        return proposal
                except (json.JSONDecodeError, TypeError):
                    continue
        
        return None