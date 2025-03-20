import multiprocessing

from flask import Flask
from gunicorn.app.base import BaseApplication

from exceptions import MultipleGunicornManager


class GunicornManager(BaseApplication):

    def __init__(self, flask_app):
            self._app = flask_app
            self.host = "0.0.0.0"
            self.port = 5000
            self.options = {
                "bind": f"{self.host}:{self.port}",
                "workers": multiprocessing.cpu_count() * 2,# maybe an overshoot
                "worker_class": "eventlet",
                "timeout": 180
            }

            super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self._app
