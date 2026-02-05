from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioResponse,
    ScenarioWithRootCause
)
from app.schemas.root_cause import RootCauseResponse
from app.services.scenario_service import (
    create_scenario_with_auto_root_cause,
    get_scenario_by_id,
    get_all_scenarios,
    get_scenarios_by_root_cause,
    update_scenario,
    link_scenario_to_root_cause,
    delete_scenario,
    search_scenarios
)
from app.services.root_cause_service import get_root_cause_by_id
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

@router.post("/", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_new_scenario(
    scenario_data: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new scenario (owned by current user). LLM detects root cause and links it when configured."""
    scenario = create_scenario_with_auto_root_cause(db, scenario_data, user_id=current_user.id)
    return scenario

@router.get("/", response_model=list[ScenarioResponse])
def get_all_scenarios_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    root_cause_id: int = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's scenarios with optional filtering"""
    if search:
        scenarios = search_scenarios(db, search_term=search, user_id=current_user.id, skip=skip, limit=limit)
    elif root_cause_id:
        scenarios = get_scenarios_by_root_cause(db, root_cause_id=root_cause_id, user_id=current_user.id, skip=skip, limit=limit)
    else:
        scenarios = get_all_scenarios(db, user_id=current_user.id, skip=skip, limit=limit)

    return scenarios

@router.get("/{scenario_id}", response_model=ScenarioWithRootCause)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scenario by ID (only own scenarios)"""
    scenario = get_scenario_by_id(db, scenario_id, user_id=current_user.id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    # Get root cause if linked
    root_cause = None
    if scenario.root_cause_id:
        root_cause = get_root_cause_by_id(db, scenario.root_cause_id)
    
    # Create response with root cause
    response = ScenarioWithRootCause.model_validate(scenario)
    if root_cause:
        response.root_cause = RootCauseResponse.model_validate(root_cause)
    
    return response

@router.put("/{scenario_id}", response_model=ScenarioResponse)
def update_scenario_info(
    scenario_id: int,
    scenario_data: ScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update scenario (only own scenarios)"""
    scenario = update_scenario(db, scenario_id, scenario_data, user_id=current_user.id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    return scenario

@router.post("/{scenario_id}/link-root-cause/{root_cause_id}", response_model=ScenarioResponse)
def link_scenario_to_root_cause_endpoint(
    scenario_id: int,
    root_cause_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Link a scenario to a root cause (only own scenarios)"""
    root_cause = get_root_cause_by_id(db, root_cause_id)
    if not root_cause:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Root cause not found"
        )

    scenario = link_scenario_to_root_cause(db, scenario_id, root_cause_id, user_id=current_user.id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    return scenario

@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario_by_id(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete scenario (only own scenarios)"""
    success = delete_scenario(db, scenario_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    return None
