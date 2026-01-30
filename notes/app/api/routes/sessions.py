from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.session import SessionResponse, SessionWithUser
from app.services.session_service import (
    get_session_by_token,
    get_session_by_id,
    get_user_sessions,
    is_session_valid,
    refresh_session,
    delete_session_by_token,
    delete_all_user_sessions
)
from app.services.user_service import get_user_by_id
from app.utils.auth import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/me", response_model=SessionWithUser)
def get_current_session(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current session from token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Extract token (format: "Bearer <token>" or just "<token>")
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    session = get_session_by_token(db, token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    if not is_session_valid(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # Get user details
    user = get_user_by_id(db, session.user_id)
    
    response = SessionWithUser.model_validate(session)
    if user:
        from app.schemas.user import UserResponse
        response.user = UserResponse.model_validate(user)
    
    return response

@router.get("/", response_model=list[SessionResponse])
def get_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's sessions."""
    sessions = get_user_sessions(db, user_id=current_user.id, skip=skip, limit=limit)
    return sessions

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get session by ID. Users may only view their own sessions."""
    session = get_session_by_id(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this session",
        )
    return session

@router.post("/refresh", response_model=SessionResponse)
def refresh_session_token(
    authorization: Optional[str] = Header(None),
    expires_in_hours: int = 24,
    db: Session = Depends(get_db)
):
    """Refresh session expiration time"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    session = refresh_session(db, token, expires_in_hours=expires_in_hours)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    return session

@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Logout and delete current session"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    success = delete_session_by_token(db, token)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return None

@router.delete("/user/{user_id}", status_code=status.HTTP_200_OK)
def logout_all_user_sessions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete all sessions for a user. Users may only logout their own sessions."""
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to logout other users",
        )
    count = delete_all_user_sessions(db, user_id)
    return {"message": f"Deleted {count} session(s)"}
