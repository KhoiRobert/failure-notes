from sqlalchemy.orm import Session
from app.models.root_cause import RootCause
from app.schemas.root_cause import RootCauseCreate, RootCauseUpdate
from typing import Optional, List

def create_root_cause(db: Session, root_cause_data: RootCauseCreate) -> RootCause:
    """Create a new root cause"""
    db_root_cause = RootCause(
        title=root_cause_data.title,
        description=root_cause_data.description,
        solution=root_cause_data.solution,
    )
    db.add(db_root_cause)
    db.commit()
    db.refresh(db_root_cause)
    return db_root_cause

def get_root_cause_by_id(db: Session, root_cause_id: int) -> Optional[RootCause]:
    """Get root cause by ID"""
    return db.query(RootCause).filter(RootCause.id == root_cause_id).first()

def get_all_root_causes(db: Session, skip: int = 0, limit: int = 100) -> List[RootCause]:
    """Get all root causes with pagination"""
    return db.query(RootCause).offset(skip).limit(limit).all()

def update_root_cause(db: Session, root_cause_id: int, root_cause_data: RootCauseUpdate) -> Optional[RootCause]:
    """Update root cause (full update, for admin/internal use)"""
    db_root_cause = get_root_cause_by_id(db, root_cause_id)
    if not db_root_cause:
        return None

    update_data = root_cause_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_root_cause, field, value)

    db.commit()
    db.refresh(db_root_cause)
    return db_root_cause

def update_root_cause_solution(db: Session, root_cause_id: int, solution: Optional[str]) -> Optional[RootCause]:
    """Update only the solution/recommendation field (user permission)"""
    db_root_cause = get_root_cause_by_id(db, root_cause_id)
    if not db_root_cause:
        return None
    db_root_cause.solution = solution
    db.commit()
    db.refresh(db_root_cause)
    return db_root_cause

def delete_root_cause(db: Session, root_cause_id: int) -> bool:
    """Delete a root cause"""
    db_root_cause = get_root_cause_by_id(db, root_cause_id)
    if not db_root_cause:
        return False
    db.delete(db_root_cause)
    db.commit()
    return True

def search_root_causes(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[RootCause]:
    """Search root causes by title or description"""
    return db.query(RootCause).filter(
        (RootCause.title.ilike(f"%{search_term}%")) |
        (RootCause.description.ilike(f"%{search_term}%"))
    ).offset(skip).limit(limit).all()

