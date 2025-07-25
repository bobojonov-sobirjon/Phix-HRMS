from sqlalchemy import Column, Integer, String
from ..database import Base

class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) 