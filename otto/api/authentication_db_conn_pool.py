import mysql.connector


class AuthenticationDbConnPool:
    def __init__(self):
        self._db_config = {
            'user': 'root', 'password': 'root',
            'host': 'localhost', 'port': 3306,
            'database': 'authentication_db'}
        self.pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="auth_db_pool",
                                                                pool_size=3,
                                                                autocommit=True,
                                                                **self._db_config)
