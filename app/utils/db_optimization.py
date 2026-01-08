"""
Database query optimization utilities
"""
from typing import List, TypeVar, Type, Optional
from sqlalchemy.orm import Session, Query
from sqlalchemy import and_, or_, in_
from sqlalchemy.orm import selectinload, joinedload
from ..core.logging_config import logger
from ..core.constants import SLOW_QUERY_THRESHOLD_SECONDS
import time

T = TypeVar('T')


def batch_get_by_ids(
    db: Session,
    model: Type[T],
    ids: List[int],
    include_deleted: bool = False
) -> List[T]:
    """
    Batch get entities by IDs to avoid N+1 queries
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        ids: List of entity IDs
        include_deleted: Whether to include deleted entities
        
    Returns:
        List of entities
    """
    if not ids:
        return []
    
    query = db.query(model).filter(model.id.in_(ids))
    
    if hasattr(model, 'is_deleted') and not include_deleted:
        query = query.filter(model.is_deleted == False)
    
    return query.all()


def optimize_query_with_eager_loading(
    query: Query,
    relationships: List[str],
    use_selectin: bool = True
) -> Query:
    """
    Add eager loading to query to prevent N+1 problems
    
    Args:
        query: SQLAlchemy query object
        relationships: List of relationship names to eager load
        use_selectin: Whether to use selectinload (True) or joinedload (False)
        
    Returns:
        Optimized query with eager loading
    """
    loader = selectinload if use_selectin else joinedload
    
    for relationship in relationships:
        try:
            if '.' in relationship:
                parts = relationship.split('.')
                current_loader = loader(getattr(query.column_descriptions[0]['entity'], parts[0]))
                for part in parts[1:]:
                    current_loader = current_loader.selectinload(getattr(current_loader.path[-1].class_, part))
                query = query.options(current_loader)
            else:
                query = query.options(loader(getattr(query.column_descriptions[0]['entity'], relationship)))
        except AttributeError:
            logger.warning(f"Relationship '{relationship}' not found, skipping eager load")
    
    return query


def execute_with_timing(query: Query, description: str = "Query") -> tuple:
    """
    Execute query with timing to detect slow queries
    
    Args:
        query: SQLAlchemy query object
        description: Description of the query for logging
        
    Returns:
        Tuple of (results, execution_time)
    """
    start_time = time.time()
    results = query.all()
    execution_time = time.time() - start_time
    
    if execution_time > SLOW_QUERY_THRESHOLD_SECONDS:
        logger.warning(
            f"Slow query detected: {description} took {execution_time:.3f}s",
            extra={
                "query_description": description,
                "execution_time": execution_time,
                "threshold": SLOW_QUERY_THRESHOLD_SECONDS
            }
        )
    
    return results, execution_time


def batch_create(
    db: Session,
    model: Type[T],
    items: List[dict],
    batch_size: int = 100
) -> List[T]:
    """
    Batch create entities to improve performance
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        items: List of dictionaries with entity data
        batch_size: Number of items to insert per batch
        
    Returns:
        List of created entities
    """
    created_items = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        instances = [model(**item) for item in batch]
        db.add_all(instances)
        created_items.extend(instances)
    
    try:
        db.commit()
        for instance in created_items:
            db.refresh(instance)
        return created_items
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch_create: {e}", exc_info=True)
        raise


def batch_update(
    db: Session,
    model: Type[T],
    updates: List[dict],
    id_field: str = "id"
) -> int:
    """
    Batch update entities
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        updates: List of dictionaries with id and fields to update
        id_field: Name of the ID field
        
    Returns:
        Number of updated entities
    """
    if not updates:
        return 0
    
    update_dict = {item[id_field]: {k: v for k, v in item.items() if k != id_field} for item in updates}
    ids = list(update_dict.keys())
    
    entities = db.query(model).filter(getattr(model, id_field).in_(ids)).all()
    
    updated_count = 0
    for entity in entities:
        entity_id = getattr(entity, id_field)
        if entity_id in update_dict:
            for key, value in update_dict[entity_id].items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            updated_count += 1
    
    try:
        db.commit()
        return updated_count
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch_update: {e}", exc_info=True)
        raise
