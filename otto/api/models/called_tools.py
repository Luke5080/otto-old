from otto.api.authentication_db import authentication_db


class CalledTools(authentication_db.Model):
    __tablename__ = "called_tools"

    id = authentication_db.Column(authentication_db.Integer, nullable=False, primary_key=True)
    agent_run = authentication_db.Column(authentication_db.String(255),
                                         authentication_db.ForeignKey('processed_intents.agent_run'), nullable=False)
    run_order = authentication_db.Column(authentication_db.Integer, nullable=False)
    tool_call_id = authentication_db.Column(authentication_db.Integer,
                                            authentication_db.ForeignKey('tool_calls.id'), nullable=False)
    arguments = authentication_db.Column(authentication_db.JSON, nullable=False)

    tool_call = authentication_db.relationship('ToolCalls', back_populates='outcomes')
    intent = authentication_db.relationship('ProcessedIntents', back_populates='outcomes')

    __table_args__ = (
        authentication_db.UniqueConstraint('agent_run', 'run_order', name='uq_agent_run_step_order'),
    )
