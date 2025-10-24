from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ProposalAttachment(Base):
    __tablename__ = "proposal_attachments"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=False)
    attachment = Column(String, nullable=False)  # File path
    size = Column(Integer, nullable=False)  # File size in bytes
    name = Column(String, nullable=False)  # Original file name
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    proposal = relationship("Proposal", back_populates="attachments")
    
    def __repr__(self):
        return f"<ProposalAttachment(id={self.id}, proposal_id={self.proposal_id}, name={self.name})>"
