from otto.api.models.base import Base
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey, Text, DateTime, JSON, UniqueConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

class ToolCalls(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(200), nullable=False)

    outcomes = relationship('CalledTools', back_populates='tool_call', cascade='all, delete-orphan')

    def populate_tool_calls():
        engine = create_engine("mysql+pymysql://root:root@127.0.0.1:3306/authentication_db")
        session = Session(engine)


        registered_tool_calls = session.query(ToolCalls).all()

        tools = [tool.name for tool in create_tool_list()]

        for registered_tool in registered_tool_calls:
            if registered_tool.name not in tools:
               tool_call = ToolCalls(name=tool)

               session.add(tool_call)

        session.commit()
