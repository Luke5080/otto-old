import enum

from werkzeug.security import generate_password_hash, check_password_hash

from otto.api.authentication_db import authentication_db


class EntityType(enum.Enum):
    USER = "User"
    APPLICATION = "Application"


class Entities(authentication_db.Model):
    __tablename__ = "entities"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True)
    username = authentication_db.Column(authentication_db.String(255), nullable=False, unique=True)
    password = authentication_db.Column(authentication_db.String(255), nullable=False)
    entity_type = authentication_db.Column(authentication_db.Enum(EntityType), nullable=False)

    user_intent = authentication_db.relationship("ProcessedIntents", back_populates="declared_user",
                                                 cascade='all, delete-orphan')

    def set_password(self, provided_password):
        self.password = generate_password_hash(provided_password)

    def check_password(self, provided_password):
        return check_password_hash(self.password_hash, provided_password)
