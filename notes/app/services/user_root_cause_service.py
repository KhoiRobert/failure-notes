import logging
from sqlalchemy.orm import Session
from app.models.user_root_cause import UserRootCause
from typing import Optional, List, Dict
from app.config import settings
from app.services.user_service import get_user_by_id
from app.services.root_cause_service import get_root_cause_by_id
from app.utils.email_service import send_usage_alert_email

logger = logging.getLogger(__name__)


def increment_usage_or_create_link(db: Session, user_id: int, root_cause_id: int) -> int:
    """
    When user creates scenario with root_cause: if user_root_cause exists, increment usage_count; 
    else create with 1. Returns new count.
    
    Sends email alert when usage_count crosses EMAIL_ALERT_THRESHOLD (default: 2).
    Alert is sent only when crossing the threshold (e.g., when count goes from 2 to 3).
    """
    link = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id,
    ).first()
    
    if link:
        old_count = link.usage_count
        link.usage_count += 1
        new_count = link.usage_count
        db.commit()
        db.refresh(link)
        
        # Send email alert only when crossing the threshold
        should_alert = old_count <= settings.EMAIL_ALERT_THRESHOLD < new_count
    else:
        link = UserRootCause(user_id=user_id, root_cause_id=root_cause_id)  # default usage_count=1
        db.add(link)
        db.commit()
        db.refresh(link)
        new_count = link.usage_count
        # For new links, check if initial count exceeds threshold (shouldn't happen with default=1)
        should_alert = new_count > settings.EMAIL_ALERT_THRESHOLD
    
    # Send email alert if threshold was crossed
    if should_alert:
        try:
            user = get_user_by_id(db, user_id)
            root_cause = get_root_cause_by_id(db, root_cause_id)
            
            if user and root_cause:
                # Send email alert asynchronously (fire and forget)
                # We don't want email failures to block the scenario creation
                send_usage_alert_email(
                    user_email=user.email,
                    username=user.username,
                    root_cause_title=root_cause.title,
                    root_cause_description=root_cause.description,
                    root_cause_solution=root_cause.solution,
                    usage_count=new_count,
                )
            else:
                logger.warning(
                    "Cannot send usage alert: user_id=%s or root_cause_id=%s not found",
                    user_id,
                    root_cause_id,
                )
        except Exception as e:
            # Log error but don't fail the operation
            logger.error(
                "Failed to send usage alert email for user_id=%s, root_cause_id=%s: %s",
                user_id,
                root_cause_id,
                e,
                exc_info=True,
            )
    
    return new_count


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


def get_usage_counts_for_root_causes(db: Session, user_id: int, root_cause_ids: List[int]) -> Dict[int, int]:
    """Get usage_count per root_cause_id for the given user. Returns {root_cause_id: count}; missing ids get 0."""
    if not root_cause_ids:
        return {}
    rows = db.query(UserRootCause.root_cause_id, UserRootCause.usage_count).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id.in_(root_cause_ids),
    ).all()
    return {int(rc_id): int(count) for rc_id, count in rows}


def link_user_to_root_cause(db: Session, user_id: int, root_cause_id: int) -> UserRootCause:
    """Link a user to a root cause (explicit link; usage_count defaults to 1)"""
    existing = db.query(UserRootCause).filter(
        UserRootCause.user_id == user_id,
        UserRootCause.root_cause_id == root_cause_id
    ).first()
    
    if existing:
        return existing
    
    db_link = UserRootCause(user_id=user_id, root_cause_id=root_cause_id)
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
