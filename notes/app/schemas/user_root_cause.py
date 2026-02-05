from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

# Request schemas
class UserRootCauseCreate(BaseModel):
    user_id: int
    root_cause_id: int

# Response schemas
class UserRootCauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: int
    root_cause_id: int
    usage_count: int = 0
    created_at: datetime

class UserRootCauseWithDetails(UserRootCauseResponse):
    """User root cause with full details"""
    user: Optional[Any] = None
    root_cause: Optional[Any] = None
