from sqlalchemy.orm import Session
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate
from typing import Optional, List

def create_scenario(db: Session, scenario_data: ScenarioCreate, user_id: int) -> Scenario:
    """Create a new scenario (owned by user_id)"""
    db_scenario = Scenario(
        user_id=user_id,
        context=scenario_data.context,
        summary=scenario_data.summary,
        root_cause_id=scenario_data.root_cause_id
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def get_scenario_by_id(db: Session, scenario_id: int, user_id: Optional[int] = None) -> Optional[Scenario]:
    """Get scenario by ID. If user_id given, only return if owned by that user."""
    q = db.query(Scenario).filter(Scenario.id == scenario_id)
    if user_id is not None:
        q = q.filter(Scenario.user_id == user_id)
    return q.first()

def get_all_scenarios(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Get all scenarios for a user with pagination"""
    return db.query(Scenario).filter(Scenario.user_id == user_id).offset(skip).limit(limit).all()

def get_scenarios_by_root_cause(db: Session, root_cause_id: int, user_id: int, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Get scenarios for a specific root cause (only user's own)"""
    return db.query(Scenario).filter(
        Scenario.root_cause_id == root_cause_id,
        Scenario.user_id == user_id
    ).offset(skip).limit(limit).all()

def get_scenario_count_by_root_cause(db: Session, root_cause_id: int) -> int:
    """Get count of all scenarios linked to a root cause (for display in root cause detail)"""
    return db.query(Scenario).filter(Scenario.root_cause_id == root_cause_id).count()

def update_scenario(db: Session, scenario_id: int, scenario_data: ScenarioUpdate, user_id: int) -> Optional[Scenario]:
    """Update scenario (only if owned by user)"""
    db_scenario = get_scenario_by_id(db, scenario_id, user_id=user_id)
    if not db_scenario:
        return None

    update_data = scenario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_scenario, field, value)

    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def link_scenario_to_root_cause(db: Session, scenario_id: int, root_cause_id: int, user_id: int) -> Optional[Scenario]:
    """Link a scenario to a root cause (only if owned by user)"""
    db_scenario = get_scenario_by_id(db, scenario_id, user_id=user_id)
    if not db_scenario:
        return None

    db_scenario.root_cause_id = root_cause_id
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def delete_scenario(db: Session, scenario_id: int, user_id: int) -> bool:
    """Delete a scenario (only if owned by user)"""
    db_scenario = get_scenario_by_id(db, scenario_id, user_id=user_id)
    if not db_scenario:
        return False
    db.delete(db_scenario)
    db.commit()
    return True

def search_scenarios(db: Session, search_term: str, user_id: int, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Search scenarios by context or summary (only user's own)"""
    return db.query(Scenario).filter(
        Scenario.user_id == user_id,
        (Scenario.context.ilike(f"%{search_term}%")) |
        (Scenario.summary.ilike(f"%{search_term}%"))
    ).offset(skip).limit(limit).all()
