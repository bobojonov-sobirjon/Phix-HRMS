from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    
    full_time_jobs = relationship("FullTimeJob", foreign_keys="FullTimeJob.category_id", back_populates="category")
    gig_jobs = relationship("GigJob", foreign_keys="GigJob.category_id", back_populates="category")
    
    users_main = relationship("User", foreign_keys="User.main_category_id", back_populates="main_category")
    users_sub = relationship("User", foreign_keys="User.sub_category_id", back_populates="sub_category")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
