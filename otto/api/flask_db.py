from flask_sqlalchemy import SQLAlchemy

from otto.api.models.base import metadata

db = SQLAlchemy(metadata=metadata)
