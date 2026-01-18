from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base


class AgoraChannel(Base):
    """
    Stores Agora channel names for chat rooms.
    Token is generated fresh on each request for better security.
    """
    __tablename__ = "agora_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False, unique=True)
    channel_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    room = relationship("ChatRoom", foreign_keys=[room_id])
    
    def __repr__(self):
        return f"<AgoraChannel(id={self.id}, room_id={self.room_id}, channel_name='{self.channel_name}')>"
