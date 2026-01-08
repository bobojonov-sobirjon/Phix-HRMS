from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base


class AgoraToken(Base):
    __tablename__ = "agora_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, unique=True)
    token = Column(Text, nullable=False)
    channel_name = Column(String(255), nullable=False)
    uid = Column(Integer, nullable=True)
    role = Column(String(50), nullable=False, default="publisher")
    expire_seconds = Column(Integer, nullable=False, default=3600)
    expire_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    room = relationship("ChatRoom", foreign_keys=[room_id])
    
    def __repr__(self):
        return f"<AgoraToken(id={self.id}, room_id={self.room_id}, channel_name='{self.channel_name}')>"
