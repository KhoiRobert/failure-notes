from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any

# Request schemas
class SessionCreate(BaseModel):
    user_id: int
    token: str
    expires_at: datetime

# Response schemas
class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    token: str
    expires_at: datetime
    created_at: datetime

class SessionWithUser(SessionResponse):
    """Session with user details"""
    user: Optional[Any] = None
