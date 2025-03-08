from flask import Flask
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor

class OttoApi:
    _app: Flask
    _intent_processor: IntentProcessor

    def __init__(self, intent_processor):
        self._app = Flask(__name__)
        self._intent_processor = intent_processor