import datetime
import os
from functools import wraps

import jwt
import mysql.connector
from flask import Flask, jsonify, request
from langchain_core.messages import HumanMessage

from exceptions import MultipleFlaskApiException
from otto.ryu.intent_engine.intent_processor_pool import IntentProcessorPool


class OttoApi:
    _app: Flask
    _intent_processor_pool: IntentProcessorPool

    __instance = None

    @staticmethod
    def get_instance():
        if OttoApi.__instance is None:
            OttoApi()
        return OttoApi.__instance

    def __init__(self):
        if OttoApi.__instance is None:
            self.app = Flask(__name__)
            self._database_connection = mysql.connector.connect(
                user='root', password='root', host='localhost', port=3306, database='authentication_db'
            )
            self.app.config['SECRET_KEY'] = os.urandom(16)
            self._intent_processor_pool = IntentProcessorPool()

            self._create_routes()

            OttoApi.__instance = self
        else:
            raise MultipleFlaskApiException(f"An occurrence of OttoApi already exists at  {OttoApi.__instance}")

    def _create_routes(self):
        def validate_token(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                token = request.headers['Authorization']

                if not token:
                    return jsonify({'message': 'Access token not found'}), 403

                try:
                    token = token.split(" ")[1]
                    token_data = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])
                    print(token_data)
                except Exception as e:
                    print(e)
                    return jsonify({'message': 'Invalid token'}), 403
                return func(*args, **kwargs)

            return wrapped

        @self.app.route('/login', methods=['POST'])
        def app_login():
            login_request = request.get_json()

            if not login_request:
                return jsonify(
                    {'message': 'Empty request body. Please provide the following fields: method, username, password'}), 403

            if 'method' not in login_request or login_request['method'] not in ['application', 'user']:
                return jsonify(
                    {'message': 'Method must be set to either application or user'}), 403

            table = "network_applications" if login_request['method'] == "application" else "users"

            if 'username' not in login_request or 'password' not in login_request:
                return jsonify(
                    {'message': 'Username AND Password are required for network application authentication'}), 403

            cursor = self._database_connection.cursor()

            cursor.execute(
               f"SELECT COUNT(*) FROM {table} WHERE username = %s", (login_request['username'],)
            )

            result = cursor.fetchone()

            if result[0] == 0:
                return jsonify({'message': f"{login_request['method']} {login_request['username']} not found"}), 403

            cursor.execute(
                f"SELECT * FROM {table} where username = %s AND password = %s",
                (login_request['username'], login_request['password'])
            )

            if cursor.fetchone() is not None:
                token = jwt.encode({
                    'app': login_request['username'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3600)
                }, self.app.config['SECRET_KEY'], algorithm='HS256')
                return jsonify({'token': token})

            else:
                return jsonify(
                    {'message': f"Incorrect password for {login_request['method']} {login_request['username']}"}), 403

        @self.app.route("/declare-intent", methods=['POST'])
        @validate_token
        def process_intent():
            token = request.headers['Authorization']
            token = token.split(" ")[1]

            token_data = jwt.decode(token, self.app.config['SECRET_KEY'], algorithms=['HS256'])

            intent_request = request.get_json()

            if not intent_request or 'intent' not in intent_request:
                return jsonify({'message': 'No intent found'}), 403

            if 'model' not in intent_request:
                designated_processor = self._intent_processor_pool.get_intent_processor('gpt-4o')
            else:
                designated_processor = self._intent_processor_pool.get_intent_processor(intent_request['model'])

            designated_processor.context = token_data.get("app", {})

            intent = intent_request['intent']

            messages = [HumanMessage(content=intent)]

            result = designated_processor.graph.invoke({"messages": messages})

            print(result)

            self._intent_processor_pool.return_intent_processor(designated_processor)

            return jsonify({'message': result['operations']})

    def run(self):
        self.app.run()
