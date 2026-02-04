from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.root_cause import (
    RootCauseCreate,
    RootCauseUpdateSolution,
    RootCauseResponse,
    RootCauseWithScenarios,
    RootCauseWithUsage,
    RootCauseTitle,
)
from app.services.root_cause_service import (
    create_root_cause,
    get_root_cause_by_id,
    get_all_root_causes,
    get_all_root_cause_titles,
    update_root_cause_solution,
    search_root_causes,
)
from app.services.scenario_service import get_scenario_count_by_root_cause
from app.utils.auth import get_current_user, get_optional_user, security
from app.models.user import User
from app.services.user_root_cause_service import get_usage_counts_for_root_causes
from typing import Optional

router = APIRouter(prefix="/root-causes", tags=["root-causes"])

@router.post("/", response_model=RootCauseResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security)])
def create_new_root_cause(
    root_cause_data: RootCauseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new root cause (requires authentication)"""
    root_cause = create_root_cause(db, root_cause_data)
    return root_cause

@router.get("/", response_model=list[RootCauseWithUsage])
def get_all_root_causes_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Get all root causes with optional search filtering. Includes usage_count for authenticated users."""
    if search:
        root_causes = search_root_causes(db, search_term=search, skip=skip, limit=limit)
    else:
        root_causes = get_all_root_causes(db, skip=skip, limit=limit)

    # Batch load usage counts to avoid N+1 query problem
    usage_map = {}
    if current_user and root_causes:
        usage_map = get_usage_counts_for_root_causes(db, current_user.id, [rc.id for rc in root_causes])

    result = []
    for rc in root_causes:
        base = RootCauseResponse.model_validate(rc)
        count = usage_map.get(rc.id, 0) if current_user else None
        result.append(RootCauseWithUsage(**base.model_dump(), usage_count=count))

    # Sort: usage_count > 2 first, then by usage_count descending
    def sort_key(x: RootCauseWithUsage):
        count = x.usage_count or 0
        high_usage_first = 0 if count > 2 else 1
        return (high_usage_first, -count)

    result.sort(key=sort_key)
    return result


@router.get("/titles", response_model=list[RootCauseTitle])
def get_all_root_cause_titles_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all root causes with only id and title"""
    return get_all_root_cause_titles(db, skip=skip, limit=limit)


@router.get("/{root_cause_id}", response_model=RootCauseWithScenarios)
def get_root_cause(root_cause_id: int, db: Session = Depends(get_db)):
    """Get root cause by ID with scenario count"""
    root_cause = get_root_cause_by_id(db, root_cause_id)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    
    # Get scenario count (all users' scenarios linked to this root cause)
    scenario_count = get_scenario_count_by_root_cause(db, root_cause_id)
    
    # Create response with scenario count
    response = RootCauseWithScenarios.model_validate(root_cause)
    response.scenarios_count = scenario_count
    
    return response

@router.patch("/{root_cause_id}/solution", response_model=RootCauseResponse, dependencies=[Depends(security)])
def update_root_cause_solution_endpoint(
    root_cause_id: int,
    data: RootCauseUpdateSolution,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit recommendation/solution for a root cause (users can only edit this field)"""
    root_cause = update_root_cause_solution(db, root_cause_id, data.solution)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )
    return root_cause
