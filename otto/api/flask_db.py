from otto.api.models.base import metadata
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(metadata=metadata)
