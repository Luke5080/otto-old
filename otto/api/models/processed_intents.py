from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship

from otto.api.models.base import Base


class ProcessedIntents(Base):
    __tablename__ = "processed_intents"

    agent_run = Column(String(255), primary_key=True, nullable=False)
    declared_by_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    intent = Column(Text)
    timestamp = Column(DateTime, nullable=False)
    model = Column(String(255), nullable=False)

    declared_user = relationship("Entities", back_populates="user_intent")
    outcomes = relationship('CalledTools', back_populates='intent', cascade='all, delete-orphan')
