from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.root_cause import (
    RootCauseCreate,
    RootCauseUpdate,
    RootCauseResponse,
    RootCauseWithScenarios
)
from app.services.root_cause_service import (
    create_root_cause,
    get_root_cause_by_id,
    get_all_root_causes,
    update_root_cause,
    delete_root_cause,
    search_root_causes,
    get_root_causes_by_occurrence
)
from app.services.scenario_service import get_scenarios_by_root_cause
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/root-causes", tags=["root-causes"])

@router.post("/", response_model=RootCauseResponse, status_code=status.HTTP_201_CREATED)
def create_new_root_cause(
    root_cause_data: RootCauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Create a new root cause"""
    root_cause = create_root_cause(db, root_cause_data)
    return root_cause

@router.get("/", response_model=list[RootCauseResponse])
def get_all_root_causes_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    min_occurrence: int = Query(None, ge=1),
    db: Session = Depends(get_db)
):
    """Get all root causes with optional filtering"""
    if search:
        root_causes = search_root_causes(db, search_term=search, skip=skip, limit=limit)
    elif min_occurrence:
        root_causes = get_root_causes_by_occurrence(db, min_occurrence=min_occurrence, skip=skip, limit=limit)
    else:
        root_causes = get_all_root_causes(db, skip=skip, limit=limit)
    
    return root_causes

@router.get("/{root_cause_id}", response_model=RootCauseWithScenarios)
def get_root_cause(root_cause_id: int, db: Session = Depends(get_db)):
    """Get root cause by ID with scenario count"""
    root_cause = get_root_cause_by_id(db, root_cause_id)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    
    # Get scenario count
    scenarios = get_scenarios_by_root_cause(db, root_cause_id)
    scenario_count = len(scenarios)
    
    # Create response with scenario count
    response = RootCauseWithScenarios.model_validate(root_cause)
    response.scenarios_count = scenario_count
    
    return response

@router.put("/{root_cause_id}", response_model=RootCauseResponse)
def update_root_cause_info(
    root_cause_id: int,
    root_cause_data: RootCauseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Update root cause"""
    root_cause = update_root_cause(db, root_cause_id, root_cause_data)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    return root_cause

@router.delete("/{root_cause_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_root_cause_by_id(
    root_cause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Requires authentication
):
    """Delete root cause"""
    success = delete_root_cause(db, root_cause_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    return None
