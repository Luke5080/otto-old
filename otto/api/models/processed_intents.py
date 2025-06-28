from otto.api.authentication_db import authentication_db

class ProcessedIntents(authentication_db.Model):
    __tablename__ = "processed_intents"

    agent_run = authentication_db.Column(authentication_db.String(255), primary_key=True, nullable=False)
    declared_by_type = authentication_db.Column(authentication_db.String(100), nullable=False)
    declared_by_id = authentication_db.Column(authentication_db.Integer, nullable=False)
    intent = authentication_db.Column(authentication_db.Text)
    timestamp = authentication_db.Column(authentication_db.Datetime, nullable=False)

    outcomes = authentication_db.relationship('CalledTools', back_populates='intent', cascade='all, delete-orphan')