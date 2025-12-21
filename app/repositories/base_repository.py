"""
Base Repository Class
Provides common CRUD operations for all repositories
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
ModelType = TypeVar('ModelType', bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """
        Initialize repository
        
        Args:
            db: Database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model
    
    def get_by_id(self, id: int, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Get entity by ID
        
        Args:
            id: Entity ID
            include_deleted: Whether to include deleted entities
            
        Returns:
            Entity or None if not found
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        
        # Filter deleted entities if model has is_deleted attribute
        if hasattr(self.model, 'is_deleted') and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        return query.first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_deleted: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Get all entities with pagination
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include deleted entities
            filters: Additional filters to apply
            
        Returns:
            List of entities
        """
        query = self.db.query(self.model)
        
        # Filter deleted entities if model has is_deleted attribute
        if hasattr(self.model, 'is_deleted') and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, include_deleted: bool = False, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities
        
        Args:
            include_deleted: Whether to include deleted entities
            filters: Additional filters to apply
            
        Returns:
            Total count
        """
        query = self.db.query(self.model)
        
        # Filter deleted entities if model has is_deleted attribute
        if hasattr(self.model, 'is_deleted') and not include_deleted:
            query = query.filter(self.model.is_deleted == False)
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create new entity
        
        Args:
            data: Dictionary of entity attributes
            
        Returns:
            Created entity
        """
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def update(self, id: int, data: Any, exclude_unset: bool = True) -> Optional[ModelType]:
        """
        Update entity
        
        Args:
            id: Entity ID
            data: Dictionary of attributes to update or Pydantic model
            exclude_unset: Whether to exclude unset fields (for Pydantic models)
            
        Returns:
            Updated entity or None if not found
        """
        # Call base class method directly to avoid static method shadowing
        instance = BaseRepository.get_by_id(self, id)
        if not instance:
            return None
        
        # Handle Pydantic models
        if hasattr(data, 'dict'):
            update_data = data.dict(exclude_unset=exclude_unset)
        elif isinstance(data, dict):
            update_data = data
        else:
            # Try to convert to dict
            update_data = dict(data) if hasattr(data, '__dict__') else {}
        
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def delete(self, id: int, hard_delete: bool = False) -> bool:
        """
        Delete entity (soft delete by default)
        
        Args:
            id: Entity ID
            hard_delete: Whether to perform hard delete
            
        Returns:
            True if deleted, False if not found
        """
        # Call base class method directly to avoid static method shadowing
        # For hard delete, we need to find the entity even if soft-deleted
        # For soft delete, we only want to find non-deleted entities
        include_deleted = hard_delete
        instance = BaseRepository.get_by_id(self, id, include_deleted=include_deleted)
        if not instance:
            return False
        
        if hard_delete:
            self.db.delete(instance)
        else:
            # Soft delete if model has is_deleted attribute
            if hasattr(instance, 'is_deleted'):
                instance.is_deleted = True
            else:
                # Fallback to hard delete if soft delete not supported
                self.db.delete(instance)
        
        self.db.commit()
        return True
    
    def exists(self, id: int, include_deleted: bool = False) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            include_deleted: Whether to include deleted entities
            
        Returns:
            True if exists, False otherwise
        """
        # Call base class method directly to avoid static method shadowing
        return BaseRepository.get_by_id(self, id, include_deleted) is not None
    
    def search(
        self,
        search_field: str,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        case_sensitive: bool = False
    ) -> List[ModelType]:
        """
        Search entities by field
        
        Args:
            search_field: Field name to search in
            search_term: Search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            case_sensitive: Whether search is case sensitive
            
        Returns:
            List of matching entities
        """
        if not hasattr(self.model, search_field):
            return []
        
        query = self.db.query(self.model)
        
        # Filter deleted entities if model has is_deleted attribute
        if hasattr(self.model, 'is_deleted'):
            query = query.filter(self.model.is_deleted == False)
        
        # Apply search filter
        field = getattr(self.model, search_field)
        if case_sensitive:
            query = query.filter(field.contains(search_term))
        else:
            query = query.filter(field.ilike(f"%{search_term}%"))
        
        return query.offset(skip).limit(limit).all()
