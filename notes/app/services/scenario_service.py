import logging
from sqlalchemy.orm import Session
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate
from app.config import settings

logger = logging.getLogger(__name__)
from app.services.user_root_cause_service import increment_usage_or_create_link, decrement_usage
from app.services.root_cause_service import (
    create_root_cause as create_root_cause_record,
    get_all_root_causes,
)
from app.services.llm_root_cause_service import detect_root_cause_from_context
from typing import Optional, List


def create_scenario(
    db: Session,
    scenario_data: ScenarioCreate,
    user_id: int,
    root_cause_id: Optional[int] = None,
    summary: Optional[str] = None,
) -> Scenario:
    """Create a new scenario (owned by user_id). Optionally link to root_cause and set summary."""
    db_scenario = Scenario(
        user_id=user_id,
        context=scenario_data.context,
        root_cause_id=root_cause_id,
        summary=summary,
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario


def create_scenario_with_auto_root_cause(
    db: Session, scenario_data: ScenarioCreate, user_id: int
) -> Scenario:
    """
    Workflow:
    1. If AI is disabled (no API key), create scenario without root cause and return.
    2. Load existing root causes; detect_root_cause_from_context matches context to one or creates new.
    3. Use validated existing_id or create new root cause from create_data.
    4. Create scenario (with or without root_cause_id) and link user usage when linked.
    """
    logger.info("create_scenario_with_auto_root_cause called (context length=%d)", len(scenario_data.context or ""))

    api_key = (getattr(settings, "AI_API_KEY", None) or "").strip()
    if not api_key:
        logger.info("AI_API_KEY not set; creating scenario without root cause")
        return create_scenario(db, scenario_data, user_id=user_id)

    existing_root_causes = get_all_root_causes(db, skip=0, limit=300)
    valid_ids = {rc.id for rc in existing_root_causes} if existing_root_causes else set()
    result = detect_root_cause_from_context(
        scenario_data.context,
        existing_root_causes=existing_root_causes,
    )

    root_cause_id: Optional[int] = None
    if result.existing_id and result.existing_id in valid_ids:
        root_cause_id = result.existing_id
        logger.info("Using existing root_cause_id=%s", root_cause_id)
    elif result.create_data:
        new_root_cause = create_root_cause_record(db, result.create_data)
        root_cause_id = new_root_cause.id
        logger.info("Created new root_cause id=%s title=%s", root_cause_id, new_root_cause.title)
    else:
        logger.warning("No root cause linked (LLM unavailable or no match; scenario still created)")

    scenario = create_scenario(
        db,
        scenario_data,
        user_id=user_id,
        root_cause_id=root_cause_id,
    )
    if root_cause_id is not None:
        increment_usage_or_create_link(db, user_id=user_id, root_cause_id=root_cause_id)
    return scenario

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
    """Update scenario (only if owned by user). Root cause changes via link/unlink endpoints."""
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

    old_root_cause_id = db_scenario.root_cause_id
    db_scenario.root_cause_id = root_cause_id
    db.commit()
    db.refresh(db_scenario)
    if old_root_cause_id != root_cause_id:
        if old_root_cause_id:
            decrement_usage(db, user_id=user_id, root_cause_id=old_root_cause_id)
        increment_usage_or_create_link(db, user_id=user_id, root_cause_id=root_cause_id)
    return db_scenario

def delete_scenario(db: Session, scenario_id: int, user_id: int) -> bool:
    """Delete a scenario (only if owned by user)"""
    db_scenario = get_scenario_by_id(db, scenario_id, user_id=user_id)
    if not db_scenario:
        return False
    root_cause_id = db_scenario.root_cause_id
    db.delete(db_scenario)
    db.commit()
    if root_cause_id:
        decrement_usage(db, user_id=user_id, root_cause_id=root_cause_id)
    return True

def search_scenarios(db: Session, search_term: str, user_id: int, skip: int = 0, limit: int = 100) -> List[Scenario]:
    """Search scenarios by context or summary (only user's own)"""
    return db.query(Scenario).filter(
        Scenario.user_id == user_id,
        (Scenario.context.ilike(f"%{search_term}%")) |
        (Scenario.summary.ilike(f"%{search_term}%"))
    ).offset(skip).limit(limit).all()
