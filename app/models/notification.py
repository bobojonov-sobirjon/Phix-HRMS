from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class NotificationType(str, enum.Enum):
    APPLICATION = "application"
    PROPOSAL_VIEWED = "proposal_viewed"
    CHAT_MESSAGE = "chat_message"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    type = Column(Enum(NotificationType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    job_id = Column(Integer, nullable=True)
    job_type = Column(String(20), nullable=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    recipient = relationship("User", foreign_keys=[recipient_user_id], back_populates="notifications")
    proposal = relationship("Proposal", back_populates="notifications")
    applicant = relationship("User", foreign_keys=[applicant_id])
    sender = relationship("User", foreign_keys=[sender_id])
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, recipient_user_id={self.recipient_user_id}, is_read={self.is_read})>"

