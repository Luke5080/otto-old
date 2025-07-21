import enum

from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from otto.api.models.base import Base


class EntityType(enum.Enum):
    USER = "User"
    APPLICATION = "Application"


class Entities(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    entity_type = Column(Enum(EntityType), nullable=False)

    user_intent = relationship("ProcessedIntents", back_populates="declared_user",
                               cascade='all, delete-orphan')

    def set_password(self, provided_password: str) -> None:
        self.password = generate_password_hash(provided_password)

    def check_password(self, provided_password: str) -> bool:
        return check_password_hash(self.password, provided_password)
