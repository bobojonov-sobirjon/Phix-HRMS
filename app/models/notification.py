from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationType(str, enum.Enum):
    APPLICATION = "application"  # When someone applies to your job
    PROPOSAL_VIEWED = "proposal_viewed"  # When your proposal is viewed
    CHAT_MESSAGE = "chat_message"  # When someone sends you a chat message


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Notification details
    type = Column(Enum(NotificationType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    # Recipient (who receives the notification)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Related entities
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    job_id = Column(Integer, nullable=True)  # Can be gig_job_id or full_time_job_id
    job_type = Column(String(20), nullable=True)  # "gig" or "full_time"
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For application type
    
    # Chat-related fields
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=True)  # For chat messages
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)  # For chat messages
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For chat messages (who sent the message)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_user_id], back_populates="notifications")
    proposal = relationship("Proposal", back_populates="notifications")
    applicant = relationship("User", foreign_keys=[applicant_id])
    sender = relationship("User", foreign_keys=[sender_id])  # For chat messages
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, recipient_user_id={self.recipient_user_id}, is_read={self.is_read})>"

