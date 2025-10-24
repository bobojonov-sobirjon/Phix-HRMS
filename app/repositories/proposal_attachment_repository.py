from sqlalchemy.orm import Session
from app.models.proposal_attachment import ProposalAttachment
from typing import List, Optional


class ProposalAttachmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, proposal_id: int, attachment: str, size: int, name: str) -> ProposalAttachment:
        """Create a new proposal attachment"""
        proposal_attachment = ProposalAttachment(
            proposal_id=proposal_id,
            attachment=attachment,
            size=size,
            name=name
        )
        self.db.add(proposal_attachment)
        self.db.commit()
        self.db.refresh(proposal_attachment)
        return proposal_attachment

    def get_by_proposal_id(self, proposal_id: int) -> List[ProposalAttachment]:
        """Get all attachments for a proposal"""
        return self.db.query(ProposalAttachment).filter(
            ProposalAttachment.proposal_id == proposal_id
        ).all()

    def delete_by_proposal_id(self, proposal_id: int) -> bool:
        """Delete all attachments for a proposal"""
        attachments = self.db.query(ProposalAttachment).filter(
            ProposalAttachment.proposal_id == proposal_id
        ).all()
        
        for attachment in attachments:
            self.db.delete(attachment)
        
        self.db.commit()
        return True

    def delete_by_id(self, attachment_id: int) -> bool:
        """Delete a specific attachment by ID"""
        attachment = self.db.query(ProposalAttachment).filter(
            ProposalAttachment.id == attachment_id
        ).first()
        
        if attachment:
            self.db.delete(attachment)
            self.db.commit()
            return True
        return False
