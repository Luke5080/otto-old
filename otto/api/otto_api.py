import os
from functools import wraps

import jwt
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig

from otto.api.authentication_db_conn_pool import AuthenticationDbConnPool
from otto.otto_logger.logger_config import logger
from otto.ryu.intent_engine.intent_processor_pool import IntentProcessorPool
from otto.ryu.network_state_db.processed_intents_db_operator import ProcessedIntentsDbOperator

authentication_db = SQLAlchemy()

class OttoApi:
    _app: Flask
    _intent_processor_pool: IntentProcessorPool
    _authentication_db_pool: AuthenticationDbConnPool

    def __init__(self, models: list[str] = None, pool_size: int = None):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = os.urandom(16)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@127.0.0.1:3306/authentication_db"
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        authentication_db.init_app(self.app)

        self._processed_intents_db_conn = ProcessedIntentsDbOperator()

        self._intent_processor_pool = IntentProcessorPool()

        self._authentication_db_pool = AuthenticationDbConnPool()

        self._create_routes()

    def _create_routes(self):
        """ Creates route to be used by Flask app"""

        def validate_token(func):
            """
            Function to valid JWT token passed in each request after /login
            """

            @wraps(func)
            def wrapped(*args, **kwargs):
                token = request.headers['Authorization']

                if not token:
                    return jsonify({'message': 'Access token not found'}), 403

                try:
                    token = token.split(" ")[1]
                    token_data = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])

                except Exception as e:
                    logger.warn(e)
                    return jsonify({'message': 'Invalid token'}), 403

                return func(*args, **kwargs)

            return wrapped

        @self.app.route('/login', methods=['POST'])
        def app_login():
            """
            Login function to authenticate a user/network application before using northbound interface.
            The /login route is used by the streamlit dashboard to authenticate a user, as well as being used to
            authenticate network applications which consume the different REST API endpoints. Returns a JWT token
            to be used in subsequent API calls.

            Fields to be added in POST request body:
                method: Context for the login API call. Should be either application or username. This is needed to know
                which table to query against.
                username: Username for the user or the registered application name
                password: Password for the associated user/application.

            """

            login_request = request.get_json()

            if not login_request:
                return jsonify(
                    {
                        'message': 'Empty request body. Please provide the following fields: method (either application or user), username, password'
                    }), 403

            if 'method' not in login_request or login_request['method'] not in ['application', 'user']:
                return jsonify(
                    {'message': 'Method must be set to either application or user'}), 403

            if 'username' not in login_request or 'password' not in login_request:
                return jsonify(
                    {'message': 'Username AND Password are required for network application authentication'}), 403

            table = "network_applications" if login_request['method'] == "application" else "users"

            """
            conn = self._authentication_db_pool.pool.get_connection()
            cursor = None

            try:

                cursor = conn.cursor(buffered=True)

                cursor.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE username = %s", (login_request['username'],)
                )

                result = cursor.fetchone()

                if result[0] == 1:
                    cursor.execute(
                        f"SELECT * FROM {table} where username = %s AND password = %s",
                        (login_request['username'], login_request['password'])
                    )

            finally:
                if cursor is not None:
                    cursor.close()

                conn.close()

            if cursor.fetchone() is not None:
                token = jwt.encode({
                    'app': login_request['username'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)
                }, self.app.config['SECRET_KEY'], algorithm='HS256')

                return jsonify({'token': token})

            else:
                return jsonify(
                    {
                        'message': f"Incorrect username/password for {login_request['method']} {login_request['username']}"}), 403
        """

        @self.app.route("/declare-intent", methods=['POST'])
        @validate_token
        def process_intent():
            token = request.headers['Authorization']
            token = token.split(" ")[1]
            token_data = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])

            intent_request = request.get_json()
            if not intent_request or 'intent' not in intent_request:
                return jsonify({'message': 'No intent found'}), 403

            if 'model' not in intent_request or intent_request['model'] is None:
                designated_processor = self.intent_processor_pool.get_intent_processor('gpt-4o')
            else:
                designated_processor = self.intent_processor_pool.get_intent_processor(intent_request['model'])

            designated_processor.context = token_data.get("app", {})

            intent = intent_request['intent']

            messages = [HumanMessage(content=intent)]

            config = RunnableConfig(recursion_limit=300)

            result = designated_processor.graph.invoke({"messages": messages}, config)
            resp = ""
            for m in result['messages']:
                if isinstance(m, AIMessage):
                    if isinstance(m.content, str):
                        resp += m.content + " "
                    else:
                        resp += m.content[0].get("text", "") + " "

            self.intent_processor_pool.return_intent_processor(designated_processor)

            if 'stream_type' in intent_request and 'stream_type' == 'AgentMessages':
                return jsonify({'message': resp, 'operations': result['operations']})
            else:
                return jsonify({'message': resp, 'operations': result['operations']})

        @self.app.route('/latest-activity', methods=['GET'])
        @validate_token
        def get_latest_activity():
            self._processed_intents_db_conn.connect()
            response = self._processed_intents_db_conn.get_latest_activity()

            return jsonify({'message': response})

        @self.app.route('/weekly-activity', methods=['GET'])
        @validate_token
        def get_weekly_activity():
            self._processed_intents_db_conn.connect()
            response = self._processed_intents_db_conn.get_weekly_activity()

            return jsonify({'message': response})

        @self.app.route('/top-activity', methods=['GET'])
        @validate_token
        def get_top_activity():
            self._processed_intents_db_conn.connect()
            response = self._processed_intents_db_conn.get_top_activity()

            return jsonify({'message': response})

        @self.app.route('/model-usage', methods=['GET'])
        @validate_token
        def get_model_activity():
            self._processed_intents_db_conn.connect()
            response = self._processed_intents_db_conn.get_model_usage()

            return jsonify({'message': response})

    def run(self):
        self.app.run()
