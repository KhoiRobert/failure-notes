from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# Request schemas
class RootCauseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    solution: Optional[str] = None

class RootCauseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    occurrence_count: Optional[int] = None

# Response schemas
class RootCauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: Optional[str]
    solution: Optional[str]
    occurrence_count: int
    created_at: datetime
    updated_at: datetime

class RootCauseWithScenarios(RootCauseResponse):
    """Root cause with related scenarios count"""
    scenarios_count: Optional[int] = None
