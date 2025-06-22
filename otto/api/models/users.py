from otto.api.otto_api import authentication_db


class Users(authentication_db.Model):
    __tablename__ = "users"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True)
    username = authentication_db.Column(authentication_db.String(255), nullable=False, unique=True)
    password = authentication_db.Column(authentication_db.String(255), nullable=False)
