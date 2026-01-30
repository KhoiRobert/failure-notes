from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

# Request schemas
class ScenarioCreate(BaseModel):
    context: str
    summary: Optional[str] = None
    root_cause_id: Optional[int] = None

class ScenarioUpdate(BaseModel):
    context: Optional[str] = None
    summary: Optional[str] = None
    root_cause_id: Optional[int] = None

# Response schemas
class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    root_cause_id: Optional[int]
    context: str
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

class ScenarioWithRootCause(ScenarioResponse):
    """Scenario with root cause details"""
    root_cause: Optional[Any] = None
