from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.base import Base
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing basic CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db_session: Session):
        self.model = model
        self.db_session = db_session
    
    def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        try:
            db_obj = self.model(**kwargs)
            self.db_session.add(db_obj)
            self.db_session.commit()
            self.db_session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
    
    def get(self, id: str) -> Optional[ModelType]:
        """Get a record by ID."""
        return self.db_session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination."""
        return self.db_session.query(self.model).offset(skip).limit(limit).all()
    
    def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """Update a record."""
        try:
            db_obj = self.get(id)
            if db_obj:
                for key, value in kwargs.items():
                    setattr(db_obj, key, value)
                self.db_session.commit()
                self.db_session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise
    
    def delete(self, id: str) -> bool:
        """Delete a record."""
        try:
            db_obj = self.get(id)
            if db_obj:
                self.db_session.delete(db_obj)
                self.db_session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise
    
    def count(self, **filters) -> int:
        """Count records with optional filters."""
        query = self.db_session.query(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.count()
    
    def find_by(self, **filters) -> List[ModelType]:
        """Find records by filters."""
        query = self.db_session.query(self.model)
        for key, value in filters.items():
            query = query.filter(getattr(self.model, key) == value)
        return query.all()
    
    def exists(self, **filters) -> bool:
        """Check if a record exists."""
        return self.count(**filters) > 0