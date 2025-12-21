from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..repositories.language_repository import LanguageRepository
from ..schemas.language import LanguageResponse, LanguageCreate, LanguageUpdate
from ..schemas.common import SuccessResponse
from ..utils.decorators import handle_errors
from ..utils.response_helpers import success_response, not_found_error, validate_entity_exists
from ..models.user import User
from ..utils.auth import get_current_user

router = APIRouter(prefix="/languages", tags=["Languages"])

@router.get("/{language_id}", response_model=SuccessResponse)
@handle_errors
async def get_language(
    language_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get language by ID"""
    repo = LanguageRepository(db)
    lang = repo.get_language_by_id(language_id)
    validate_entity_exists(lang, "Language")
    return success_response(
        data=LanguageResponse.model_validate(lang),
        message="Language retrieved successfully"
    )

@router.get("/", response_model=SuccessResponse)
@handle_errors
async def get_languages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all languages"""
    repo = LanguageRepository(db)
    langs = repo.get_all_languages()
    languages = [LanguageResponse.model_validate(l) for l in langs]
    return success_response(
        data=languages,
        message="Languages retrieved successfully"
    )

@router.post("/", response_model=SuccessResponse)
@handle_errors
async def create_language(
    language: LanguageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new language"""
    repo = LanguageRepository(db)
    lang = repo.create_language(language.name)
    return success_response(
        data=LanguageResponse.model_validate(lang),
        message="Language created successfully"
    )

@router.put("/{language_id}", response_model=SuccessResponse)
@handle_errors
async def update_language(
    language_id: int,
    language: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update language"""
    repo = LanguageRepository(db)
    lang = repo.update_language(language_id, language.name)
    validate_entity_exists(lang, "Language")
    return success_response(
        data=LanguageResponse.model_validate(lang),
        message="Language updated successfully"
    )

@router.delete("/{language_id}", response_model=SuccessResponse)
@handle_errors
async def delete_language(
    language_id: int,
    db: Session = Depends(get_db)
):
    """Delete language"""
    repo = LanguageRepository(db)
    success = repo.delete(language_id)
    if not success:
        raise not_found_error("Language not found")
    return success_response(
        data=None,
        message="Language deleted successfully"
    )
