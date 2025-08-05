from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..repositories.language_repository import LanguageRepository
from ..schemas.language import LanguageResponse, LanguageCreate, LanguageUpdate
from ..schemas.common import SuccessResponse
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/languages", tags=["Languages"])

@router.get("/{language_id}", response_model=SuccessResponse)
def get_language(language_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = LanguageRepository(db)
        lang = repo.get_language_by_id(language_id)
        if not lang or lang.is_deleted:
            raise HTTPException(status_code=404, detail="Language not found")
        return SuccessResponse(
            msg="Language retrieved successfully",
            data=LanguageResponse.model_validate(lang)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=SuccessResponse)
def get_languages(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = LanguageRepository(db)
        langs = repo.get_all_languages()
        languages = [LanguageResponse.model_validate(l) for l in langs]
        return SuccessResponse(
            msg="Languages retrieved successfully",
            data=languages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SuccessResponse)
def create_language(language: LanguageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = LanguageRepository(db)
        lang = repo.create_language(language.name)
        return SuccessResponse(
            msg="Language created successfully",
            data=LanguageResponse.model_validate(lang)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{language_id}", response_model=SuccessResponse)
def update_language(language_id: int, language: LanguageUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        repo = LanguageRepository(db)
        lang = repo.update_language(language_id, language.name)
        if not lang:
            raise HTTPException(status_code=404, detail="Language not found")
        return SuccessResponse(
            msg="Language updated successfully",
            data=LanguageResponse.model_validate(lang)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{language_id}", response_model=SuccessResponse)
def delete_language(language_id: int, db: Session = Depends(get_db)):
    try:
        repo = LanguageRepository(db)
        success = repo.delete(language_id)
        if not success:
            raise HTTPException(status_code=404, detail="Language not found")
        return SuccessResponse(msg="Language deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 