from sqlalchemy.orm import Session
from ..models.language import Language
from typing import Optional, List

class LanguageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, language_id: int) -> Optional[Language]:
        return self.db.query(Language).filter(Language.id == language_id).first()

    def get_all(self) -> List[Language]:
        return self.db.query(Language).all()

    def create(self, name: str) -> Language:
        language = Language(name=name)
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)
        return language

    def update(self, language_id: int, name: str) -> Optional[Language]:
        language = self.get(language_id)
        if not language:
            return None
        language.name = name
        self.db.commit()
        self.db.refresh(language)
        return language

    def delete(self, language_id: int) -> bool:
        language = self.get(language_id)
        if not language:
            return False
        self.db.delete(language)
        self.db.commit()
        return True 