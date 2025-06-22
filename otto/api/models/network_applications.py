from otto.api.authentication_db import authentication_db
from werkzeug.security import generate_password_hash, check_password_hash

class NetworkApplications(authentication_db.Model):
    __tablename__ = "network_applications"

    id = authentication_db.Column(authentication_db.Integer, primary_key=True)
    username = authentication_db.Column(authentication_db.String(255), nullable=False, unique=True)
    password = authentication_db.Column(authentication_db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
