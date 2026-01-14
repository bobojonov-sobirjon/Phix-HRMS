from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.certification_center import CertificationCenter

class CertificationCenterRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_certification_center(self, data: Dict) -> CertificationCenter:
        certification_center = CertificationCenter(**data)
        self.db.add(certification_center)
        self.db.commit()
        self.db.refresh(certification_center)
        return certification_center

    def get_certification_center_by_id(self, id: int) -> Optional[CertificationCenter]:
        return self.db.query(CertificationCenter).filter(
            CertificationCenter.id == id, 
            CertificationCenter.is_deleted == False
        ).first()

    def get_certification_center_by_name(self, name: str) -> Optional[CertificationCenter]:
        return self.db.query(CertificationCenter).filter(
            CertificationCenter.name == name, 
            CertificationCenter.is_deleted == False
        ).first()

    def get_all_certification_centers(self, skip: int = 0, limit: int = 100) -> List[CertificationCenter]:
        return self.db.query(CertificationCenter).filter(
            CertificationCenter.is_deleted == False
        ).order_by(CertificationCenter.id.asc()).offset(skip).limit(limit).all()

    def update_certification_center(self, id: int, update_data: Dict) -> Optional[CertificationCenter]:
        certification_center = self.get_certification_center_by_id(id)
        if certification_center:
            for key, value in update_data.items():
                if hasattr(certification_center, key):
                    setattr(certification_center, key, value)
            self.db.commit()
            self.db.refresh(certification_center)
        return certification_center

    def delete_certification_center(self, id: int) -> bool:
        certification_center = self.get_certification_center_by_id(id)
        if certification_center:
            certification_center.is_deleted = True
            self.db.commit()
            return True
        return False

    def search_certification_centers(self, search_term: str, skip: int = 0, limit: int = 100) -> List[CertificationCenter]:
        return self.db.query(CertificationCenter).filter(
            CertificationCenter.is_deleted == False,
            CertificationCenter.name.ilike(f"%{search_term}%")
        ).order_by(CertificationCenter.id.asc()).offset(skip).limit(limit).all()
