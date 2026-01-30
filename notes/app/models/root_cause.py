from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base

class RootCause(Base):
    __tablename__ = "root_causes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    solution = Column(Text)
    occurrence_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    scenarios = relationship("Scenario", back_populates="root_cause")
    user_root_causes = relationship("UserRootCause", back_populates="root_cause", cascade="all, delete-orphan")