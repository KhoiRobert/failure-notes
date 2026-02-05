from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class UserRootCause(Base):
    __tablename__ = "user_root_causes"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    root_cause_id = Column(Integer, ForeignKey("root_causes.id", ondelete="CASCADE"), primary_key=True, index=True)
    usage_count = Column(Integer, default=1, nullable=False)  # Scenarios user has for this root cause; +1 on create, -1 on delete
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_root_causes")
    root_cause = relationship("RootCause", back_populates="user_root_causes")
