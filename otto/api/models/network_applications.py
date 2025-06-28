from werkzeug.security import generate_password_hash, check_password_hash

from otto.api.authentication_db import authentication_db


class NetworkApplications(authentication_db.Model):
    __tablename__ = "network_applications"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True)
    username = authentication_db.Column(authentication_db.String(255), nullable=False, unique=True)
    password = authentication_db.Column(authentication_db.String(255), nullable=False)

    def set_password(self, provided_password):
        self.password = generate_password_hash(provided_password)

    def check_password(self, provided_password):
        return check_password_hash(self.password_hash, provided_password)
