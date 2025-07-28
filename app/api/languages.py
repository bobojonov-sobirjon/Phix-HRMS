from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.language_repository import LanguageRepository
from ..schemas.language import LanguageResponse, LanguageCreate, LanguageUpdate
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/languages", tags=["Languages"])

@router.get("/{language_id}", response_model=LanguageResponse)
def get_language(language_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.get_language_by_id(language_id)
    if not lang or lang.is_deleted:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.model_validate(lang)

@router.get("/", response_model=list[LanguageResponse])
def get_languages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    langs = repo.get_all_languages()
    return [LanguageResponse.model_validate(l) for l in langs]

@router.post("/", response_model=LanguageResponse)
def create_language(language: LanguageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.create_language(language.name)
    return LanguageResponse.model_validate(lang)

@router.put("/{language_id}", response_model=LanguageResponse)
def update_language(language_id: int, language: LanguageUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.update_language(language_id, language.name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.model_validate(lang)

@router.delete("/{language_id}")
def delete_language(language_id: int, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    success = repo.delete(language_id)
    if not success:
        raise HTTPException(status_code=404, detail="Language not found")
    return {"detail": "Language deleted"} 