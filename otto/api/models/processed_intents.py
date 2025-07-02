from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey, Text, DateTime, JSON, UniqueConstraint
)
from otto.api.models.base import Base
from sqlalchemy.orm import relationship

class ProcessedIntents(Base):
    __tablename__ = "processed_intents"

    agent_run = Column(String(255), primary_key=True, nullable=False)
    declared_by_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    intent =  Column(Text)
    timestamp = Column(DateTime, nullable=False)

    declared_user = relationship("Entities",back_populates="user_intent")
    outcomes = relationship('CalledTools', back_populates='intent', cascade='all, delete-orphan')
