from threading import Thread
from otto.api.otto_api import OttoApi
from otto.api.otto_gunicorn import GunicornManager


class OttoApiThread(Thread):
    def __init__(self):
        self._flask_api = OttoApi.get_instance()
        self._gunicorn_manager = GunicornManager.get_instance(self._flask_api.app)
        super().__init__()

    def run(self):
        self._gunicorn_manager.run()
