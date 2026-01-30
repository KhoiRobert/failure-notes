from sqlalchemy.orm import Session
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate
from typing import Optional, List

def create_scenario(db: Session, scenario_data: ScenarioCreate) -> Scenario:
    """Create a new scenario"""
    db_scenario = Scenario(
        context=scenario_data.context,
        summary=scenario_data.summary,
        root_cause_id=scenario_data.root_cause_id
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def get_scenario_by_id(db: Session, scenario_id: int) -> Optional[Scenario]:
    """Get scenario by ID"""
    return db.query(Scenario).filter(Scenario.id == scenario_id).first()

def get_all_scenarios(db: Session, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Get all scenarios with pagination"""
    return db.query(Scenario).offset(skip).limit(limit).all()

def get_scenarios_by_root_cause(db: Session, root_cause_id: int, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Get all scenarios for a specific root cause"""
    return db.query(Scenario).filter(
        Scenario.root_cause_id == root_cause_id
    ).offset(skip).limit(limit).all()

def update_scenario(db: Session, scenario_id: int, scenario_data: ScenarioUpdate) -> Optional[Scenario]:
    """Update scenario"""
    db_scenario = get_scenario_by_id(db, scenario_id)
    if not db_scenario:
        return None
    
    update_data = scenario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_scenario, field, value)
    
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def link_scenario_to_root_cause(db: Session, scenario_id: int, root_cause_id: int) -> Optional[Scenario]:
    """Link a scenario to a root cause"""
    db_scenario = get_scenario_by_id(db, scenario_id)
    if not db_scenario:
        return None
    
    db_scenario.root_cause_id = root_cause_id
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def delete_scenario(db: Session, scenario_id: int) -> bool:
    """Delete a scenario"""
    db_scenario = get_scenario_by_id(db, scenario_id)
    if not db_scenario:
        return False
    db.delete(db_scenario)
    db.commit()
    return True

def search_scenarios(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Search scenarios by context or summary"""
    return db.query(Scenario).filter(
        (Scenario.context.ilike(f"%{search_term}%")) |
        (Scenario.summary.ilike(f"%{search_term}%"))
    ).offset(skip).limit(limit).all()
