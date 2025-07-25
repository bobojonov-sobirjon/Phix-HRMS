from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from ..models.certification import Certification
from ..schemas.profile import CertificationCreate
from ..models.certification_center import CertificationCenter

class CertificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_certification(self, user_id: int, data: CertificationCreate) -> Certification:
        center_name = data.center_name if hasattr(data, 'center_name') else None
        center_id = None
        if center_name:
            center = self.db.query(CertificationCenter).filter(CertificationCenter.name == center_name).first()
            if not center:
                center = CertificationCenter(name=center_name, icon=None)
                self.db.add(center)
                self.db.commit()
                self.db.refresh(center)
            center_id = center.id
        cert_data = data.dict()
        cert_data.pop('center_name', None)
        cert_data['certification_center_id'] = center_id
        cert = Certification(user_id=user_id, **cert_data)
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        return cert

    def get_certification_by_id(self, id: int) -> Optional[Certification]:
        return self.db.query(Certification).filter(Certification.id == id, Certification.is_deleted == False).first()

    def get_certifications_by_user(self, user_id: int) -> List[Certification]:
        return self.db.query(Certification).filter(Certification.user_id == user_id, Certification.is_deleted == False).all()

    def update_certification(self, id: int, update_data: Dict) -> Optional[Certification]:
        cert = self.get_certification_by_id(id)
        if cert:
            for k, v in update_data.items():
                setattr(cert, k, v)
            self.db.commit()
            self.db.refresh(cert)
        return cert

    def delete_certification(self, id: int, user_id: int) -> bool:
        cert = self.get_certification_by_id(id)
        if cert and cert.user_id == user_id:
            cert.is_deleted = True
            self.db.commit()
            return True
        return False 