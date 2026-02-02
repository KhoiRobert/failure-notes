from sqlalchemy.orm import Session
from app.models.user_root_cause import UserRootCause
from app.schemas.user_root_cause import UserRootCauseCreate
from typing import Optional, List


def increment_usage_or_create_link(db: Session, user_id: int, root_cause_id: int) -> int:
    """When user creates scenario with root_cause: if user_root_cause exists, increment usage_count; else create with 1. Returns new count."""
    link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id,
    ).first()
    if link:
        link.usage_count += 1
        db.commit()
        db.refresh(link)
        return link.usage_count
    link = UserRootCause(user_id=user_id, root_cause_id=root_cause_id)  # default usage_count=1
    db.add(link)
    db.commit()
    db.refresh(link)
    return 1


def decrement_usage(db: Session, user_id: int, root_cause_id: int) -> int:
    """Decrement usage_count. Delete row if 0. Returns new count."""
    link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id,
    ).first()
    if not link:
        return 0
    link.usage_count -= 1
    if link.usage_count <= 0:
        db.delete(link)
        db.commit()
        return 0
    db.commit()
    db.refresh(link)
    return link.usage_count


def get_usage_count(db: Session, user_id: int, root_cause_id: int) -> int:
    """Get usage_count for user+root_cause. Returns 0 if no link."""
    link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id,
    ).first()
    return link.usage_count if link else 0


def link_user_to_root_cause(db: Session, user_id: int, root_cause_id: int) -> UserRootCause:
    """Link a user to a root cause (explicit link; usage_count=0 until they create scenarios)"""
    existing = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id
    ).first()
    
    if existing:
        return existing
    
    db_link = UserRootCause(user_id=user_id, root_cause_id=root_cause_id, usage_count=0)
    db.add(db_link)
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
