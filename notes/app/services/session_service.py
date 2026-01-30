from sqlalchemy.orm import Session as DBSession
from app.models.session import Session
from app.schemas.session import SessionCreate
from datetime import datetime, timedelta
from typing import Optional
import secrets

def create_session(db: DBSession, user_id: int, expires_in_hours: int = 24) -> Session:
    """Create a new session for a user"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    db_session = Session(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

def get_session_by_token(db: DBSession, token: str) -> Optional[Session]:
    """Get session by token"""
    return db.query(Session).filter(Session.token == token).first()

def get_session_by_id(db: DBSession, session_id: int) -> Optional[Session]:
    """Get session by ID"""
    return db.query(Session).filter(Session.id == session_id).first()

def get_user_sessions(db: DBSession, user_id: int, skip: int = 0, limit: int = 100):
    """Get all sessions for a user"""
    return db.query(Session).filter(
        Session.user_id == user_id
    ).offset(skip).limit(limit).all()

def is_session_valid(db: DBSession, token: str) -> bool:
    """Check if session token is valid and not expired"""
    session = get_session_by_token(db, token)
    if not session:
        return False
    if session.expires_at < datetime.utcnow():
        return False
    return True

def refresh_session(db: DBSession, token: str, expires_in_hours: int = 24) -> Optional[Session]:
    """Refresh session expiration time"""
    session = get_session_by_token(db, token)
    if not session:
        return None
    
    session.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    db.commit()
    db.refresh(session)
    return session

def delete_session(db: DBSession, session_id: int) -> bool:
    """Delete a session"""
    db_session = get_session_by_id(db, session_id)
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True

def delete_session_by_token(db: DBSession, token: str) -> bool:
    """Delete a session by token"""
    db_session = get_session_by_token(db, token)
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True

def delete_expired_sessions(db: DBSession) -> int:
    """Delete all expired sessions, returns count of deleted sessions"""
    expired_sessions = db.query(Session).filter(
        Session.expires_at < datetime.utcnow()
    ).all()
    
    count = len(expired_sessions)
    for session in expired_sessions:
        db.delete(session)
    db.commit()
    return count

def delete_all_user_sessions(db: DBSession, user_id: int) -> int:
    """Delete all sessions for a user, returns count of deleted sessions"""
    user_sessions = db.query(Session).filter(Session.user_id == user_id).all()
    count = len(user_sessions)
    for session in user_sessions:
        db.delete(session)
    db.commit()
    return count
