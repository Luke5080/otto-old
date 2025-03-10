from flask import Flask, request, jsonify
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.controller_factory import ControllerFactory


class OttoApi:
    _app: Flask
    _intent_processor: IntentProcessor

    def __init__(self):
        self._app = Flask(__name__)
        self._create_routes()

    def _create_routes(self):
        @self._app.route("/declare-intent", methods=['POST'])
        def process_intent():
            intent_request = request.get_json()

            if not intent_request or 'intent' not in intent_request:
                return jsonify({'Error': 'No intent found'})

    def run(self):
        self._app.run()
