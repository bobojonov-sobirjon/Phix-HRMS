from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.language import LanguageCreate, LanguageUpdate, LanguageResponse
from ..repositories.language_repository import LanguageRepository
from typing import List

router = APIRouter(prefix="/languages", tags=["Languages"])

@router.post("/", response_model=LanguageResponse)
def create_language(language: LanguageCreate, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.create(name=language.name)
    return LanguageResponse.from_orm(lang)

@router.get("/", response_model=List[LanguageResponse])
def get_languages(db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    langs = repo.get_all()
    return [LanguageResponse.from_orm(l) for l in langs]

@router.get("/{language_id}", response_model=LanguageResponse)
def get_language(language_id: int, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.get(language_id)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.from_orm(lang)

@router.put("/{language_id}", response_model=LanguageResponse)
def update_language(language_id: int, language: LanguageUpdate, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    lang = repo.update(language_id, name=language.name)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return LanguageResponse.from_orm(lang)

@router.delete("/{language_id}")
def delete_language(language_id: int, db: Session = Depends(get_db)):
    repo = LanguageRepository(db)
    success = repo.delete(language_id)
    if not success:
        raise HTTPException(status_code=404, detail="Language not found")
    return {"detail": "Language deleted"} 