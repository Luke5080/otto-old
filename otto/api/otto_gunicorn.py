import multiprocessing

from gunicorn.app.base import BaseApplication


class GunicornManager(BaseApplication):

    def __init__(self, flask_app):
        self._app = flask_app
        self.host = "0.0.0.0"
        self.port = 5000
        self.options = {
            "bind": f"{self.host}:{self.port}",
            "workers": multiprocessing.cpu_count() * 2,  # maybe an overshoot
            "timeout": 180,
            "loglevel": "critical" # supress all messages except critical to avoid messages being displaying when running with OttoShell
        }

        self.process = None
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self._app

    def start_in_background(self):
        if self.process is None or not self.process.is_alive():
            self.process = multiprocessing.Process(target=self.run, daemon=True)
            self.process.start()
        else:
            print("Gunicorn is already running.")

    def stop(self):
        """Stops Gunicorn if it's running."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
        else:
            print("No active Gunicorn process.")
