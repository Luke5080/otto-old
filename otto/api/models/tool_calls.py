from otto.api.authentication_db import authentication_db

class ToolCalls(authentication_db.Model):
    __tablename__ = "tool_calls"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True, unique=True)
    name = authentication_db.Column(authentication_db.String(200), nullable=False)

    outcomes = authentication_db.relationship('CalledTools', back_populates='tool_call', cascade='all, delete-orphan')

