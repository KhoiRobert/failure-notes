from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.user_root_cause import (
    UserRootCauseCreate,
    UserRootCauseResponse,
    UserRootCauseWithDetails
)
from app.services.user_root_cause_service import (
    link_user_to_root_cause,
    unlink_user_from_root_cause,
    get_user_root_causes,
    get_root_cause_users,
    is_user_linked_to_root_cause,
    get_user_root_cause_count,
    get_root_cause_user_count
)
from app.services.user_service import get_user_by_id
from app.services.root_cause_service import get_root_cause_by_id
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/user-root-causes", tags=["user-root-causes"])

@router.post("/", response_model=UserRootCauseResponse, status_code=status.HTTP_201_CREATED)
def link_user_to_root_cause_endpoint(
    link_data: UserRootCauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Link a user to a root cause"""
    # Validate user exists
    user = get_user_by_id(db, link_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate root cause exists
    root_cause = get_root_cause_by_id(db, link_data.root_cause_id)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    
    # Create link
    link = link_user_to_root_cause(db, link_data.user_id, link_data.root_cause_id)
    return link

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def unlink_user_from_root_cause_endpoint(
    user_id: int = Query(...),
    root_cause_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Unlink a user from a root cause"""
    success = unlink_user_from_root_cause(db, user_id, root_cause_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return None

@router.get("/user/{user_id}", response_model=list[UserRootCauseWithDetails])
def get_user_root_causes_list(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Get all root causes for a user"""
    # Validate user exists
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    links = get_user_root_causes(db, user_id=user_id, skip=skip, limit=limit)
    
    # Add details
    result = []
    for link in links:
        root_cause = get_root_cause_by_id(db, link.root_cause_id)
        response = UserRootCauseWithDetails.model_validate(link)
        if root_cause:
            from app.schemas.root_cause import RootCauseResponse
            response.root_cause = RootCauseResponse.model_validate(root_cause)
        result.append(response)
    
    return result

@router.get("/root-cause/{root_cause_id}", response_model=list[UserRootCauseWithDetails])
def get_root_cause_users_list(
    root_cause_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all users linked to a root cause"""
    # Validate root cause exists
    root_cause = get_root_cause_by_id(db, root_cause_id)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    
    links = get_root_cause_users(db, root_cause_id=root_cause_id, skip=skip, limit=limit)
    
    # Add details
    result = []
    for link in links:
        user = get_user_by_id(db, link.user_id)
        response = UserRootCauseWithDetails.model_validate(link)
        if user:
            from app.schemas.user import UserResponse
            response.user = UserResponse.model_validate(user)
        result.append(response)
    
    return result

@router.get("/check", response_model=dict)
def check_user_root_cause_link(
    user_id: int = Query(...),
    root_cause_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Check if user is linked to root cause"""
    is_linked = is_user_linked_to_root_cause(db, user_id, root_cause_id)
    return {
        "user_id": user_id,
        "root_cause_id": root_cause_id,
        "is_linked": is_linked
    }

@router.get("/user/{user_id}/count", response_model=dict)
def get_user_root_cause_count_endpoint(user_id: int, db: Session = Depends(get_db)):
    """Get count of root causes for a user"""
    count = get_user_root_cause_count(db, user_id)
    return {"user_id": user_id, "root_cause_count": count}

@router.get("/root-cause/{root_cause_id}/count", response_model=dict)
def get_root_cause_user_count_endpoint(root_cause_id: int, db: Session = Depends(get_db)):
    """Get count of users linked to a root cause"""
    count = get_root_cause_user_count(db, root_cause_id)
    return {"root_cause_id": root_cause_id, "user_count": count}
