from sqlalchemy import Column, Integer, String, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship

from otto.api.models.base import Base


class CalledTools(Base):
    __tablename__ = "called_tools"

    id = Column(Integer, nullable=False, primary_key=True)
    agent_run = Column(String(255), ForeignKey('processed_intents.agent_run'), nullable=False)

    run_order = Column(Integer, nullable=False)
    tool_call_id = Column(Integer, ForeignKey('tool_calls.id'), nullable=False)
    arguments = Column(JSON, nullable=False)

    tool_call = relationship('ToolCalls', back_populates='outcomes')
    intent = relationship('ProcessedIntents', back_populates='outcomes')

    __table_args__ = (
        UniqueConstraint('agent_run', 'run_order', name='uq_agent_run_step_order'),
    )
