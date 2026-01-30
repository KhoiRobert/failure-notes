from sqlalchemy.orm import Session
from app.models.user_root_cause import UserRootCause
from app.models.root_cause import RootCause
from app.schemas.user_root_cause import UserRootCauseCreate
from typing import Optional, List

def link_user_to_root_cause(db: Session, user_id: int, root_cause_id: int) -> UserRootCause:
    """Link a user to a root cause"""
    # Check if link already exists
    existing = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id
    ).first()
    
    if existing:
        return existing
    
    # Create new link
    db_link = UserRootCause(
        user_id=user_id,
        root_cause_id=root_cause_id
    )
    db.add(db_link)
    
    # Increment root cause occurrence count
    root_cause = db.query(RootCause).filter(RootCause.id == root_cause_id).first()
    if root_cause:
        root_cause.occurrence_count += 1
    
    db.commit()
    db.refresh(db_link)
    return db_link

def unlink_user_from_root_cause(db: Session, user_id: int, root_cause_id: int) -> bool:
    """Unlink a user from a root cause"""
    db_link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id
    ).first()
    
    if not db_link:
        return False
    
    db.delete(db_link)
    db.commit()
    return True

def get_user_root_causes(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[UserRootCause]:
    """Get all root causes for a user"""
    return db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_root_cause_users(db: Session, root_cause_id: int, skip: int = 0, limit: int = 100) -> List[UserRootCause]:
    """Get all users linked to a root cause"""
    return db.query(UserRootCause).filter(
        UserRootCause.root_cause_id == root_cause_id
    ).offset(skip).limit(limit).all()

def is_user_linked_to_root_cause(db: Session, user_id: int, root_cause_id: int) -> bool:
    """Check if user is linked to root cause"""
    link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id
    ).first()
    return link is not None

def get_user_root_cause_count(db: Session, user_id: int) -> int:
    """Get count of root causes for a user"""
    return db.query(UserRootCause).filter(UserRootCause.user_id == user_id).count()

def get_root_cause_user_count(db: Session, root_cause_id: int) -> int:
    """Get count of users linked to a root cause"""
    return db.query(UserRootCause).filter(UserRootCause.root_cause_id == root_cause_id).count()
