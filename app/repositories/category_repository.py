from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategorySearch


class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, category: CategoryCreate) -> Category:
        db_category = Category(
            name=category.name,
            description=category.description,
            is_active=category.is_active,
            parent_id=category.parent_id
        )
        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return self.db.query(Category).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_all_with_filter(self, is_active: bool, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all categories with active status filter"""
        return self.db.query(Category).filter(Category.is_active == is_active).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_categories_only(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get only main categories (no parent)"""
        return self.db.query(Category).filter(Category.parent_id.is_(None)).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_categories_only_with_filter(self, is_active: bool, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get only main categories (no parent) with active status filter"""
        return self.db.query(Category).filter(
            and_(Category.parent_id.is_(None), Category.is_active == is_active)
        ).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_all_subcategories(self, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all subcategories (categories with parent)"""
        return self.db.query(Category).filter(Category.parent_id.is_not(None)).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_all_subcategories_with_filter(self, is_active: bool, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get all subcategories (categories with parent) with active status filter"""
        return self.db.query(Category).filter(
            and_(Category.parent_id.is_not(None), Category.is_active == is_active)
        ).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_subcategories(self, parent_id: int, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get subcategories for a specific parent category"""
        return self.db.query(Category).filter(Category.parent_id == parent_id).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_subcategories_with_filter(self, parent_id: int, is_active: bool, skip: int = 0, limit: int = 100) -> List[Category]:
        """Get subcategories for a specific parent category with active status filter"""
        return self.db.query(Category).filter(
            and_(Category.parent_id == parent_id, Category.is_active == is_active)
        ).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def get_with_children(self, category_id: int) -> Optional[Category]:
        """Get category with all its children"""
        return self.db.query(Category).filter(Category.id == category_id).first()

    def search_by_name(self, name: str, skip: int = 0, limit: int = 100) -> List[Category]:
        """Search categories by name (case-insensitive)"""
        return self.db.query(Category).filter(
            Category.name.ilike(f"%{name}%")
        ).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def search_by_parent(self, parent_id: int, skip: int = 0, limit: int = 100) -> List[Category]:
        """Search categories by parent ID"""
        return self.db.query(Category).filter(Category.parent_id == parent_id).order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def search_categories(self, search_params: CategorySearch, skip: int = 0, limit: int = 100) -> List[Category]:
        """Advanced search with multiple parameters"""
        query = self.db.query(Category)
        
        filters = []
        
        if search_params.name:
            filters.append(Category.name.ilike(f"%{search_params.name}%"))
        
        if search_params.parent_id is not None:
            filters.append(Category.parent_id == search_params.parent_id)
        
        if search_params.is_active is not None:
            filters.append(Category.is_active == search_params.is_active)
        
        if filters:
            query = query.filter(and_(*filters))
        
        return query.order_by(Category.id.asc()).offset(skip).limit(limit).all()

    def update(self, category_id: int, category_update: CategoryUpdate) -> Optional[Category]:
        db_category = self.get_by_id(category_id)
        if not db_category:
            return None
        
        update_data = category_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_category, field, value)
        
        self.db.commit()
        self.db.refresh(db_category)
        return db_category

    def delete(self, category_id: int) -> bool:
        db_category = self.get_by_id(category_id)
        if not db_category:
            return False
        
        children = self.get_subcategories(category_id)
        if children:
            db_category.is_active = False
            self.db.commit()
            return True
        
        self.db.delete(db_category)
        self.db.commit()
        return True

    def get_category_hierarchy(self) -> List[Category]:
        """Get all categories with their hierarchy structure"""
        return self.db.query(Category).filter(Category.parent_id.is_(None)).all()

    def is_valid_parent(self, parent_id: int) -> bool:
        """Check if a category can be a valid parent (no circular references)"""
        if parent_id is None:
            return True
        
        parent = self.get_by_id(parent_id)
        if not parent or not parent.is_active:
            return False
        
        return True
