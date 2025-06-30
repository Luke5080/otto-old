from otto.api.authentication_db import authentication_db
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from otto.api.authentication_db import authentication_db

class ToolCalls(authentication_db.Model):
    __tablename__ = "tool_calls"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True, unique=True)
    name = authentication_db.Column(authentication_db.String(200), nullable=False)

    outcomes = authentication_db.relationship('CalledTools', back_populates='tool_call', cascade='all, delete-orphan')

    def populate_tool_calls():
        tools = [tool.name for tool in create_tool_list()]

        for tool in tools:
            tool_call = ToolCalls(name=tool)
            print(tool_call)
            authentication_db.session.add(tool_call)

        authentication_db.session.commit()
