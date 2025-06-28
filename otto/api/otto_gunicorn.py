import multiprocessing

from gunicorn.app.base import BaseApplication

from otto.otto_logger.logger_config import logger
from otto.api.authentication_db import authentication_db
from otto.api.models.users import Users
from otto.api.models.network_applications import NetworkApplications
from otto.api.models.tool_calls import ToolCalls
from otto.api.models.processed_intents import ProcessedIntents
from otto.api.models.called_tools import CalledTools

class GunicornManager(BaseApplication):

    def __init__(self, flask_app):
        self._app = flask_app
        self.host = "0.0.0.0"
        self.port = 5000
        self.options = {
            "bind": f"{self.host}:{self.port}",
            "workers": multiprocessing.cpu_count() * 2,
            "timeout": 3000,
            "loglevel": "critical",
            # supress all messages except critical to avoid messages being displaying when running with OttoShell
            "on_starting": self._before_fork,
            "post_fork": self._log_worker_pid
        }

        self.process = None
        super().__init__()

    def _before_fork(self, server):
        with self._app.app_context():
            try:
                authentication_db.create_all()
                logger.info("DB initialized in worker")
            except Exception as e:
                logger.warn(f"Worker DB init error: {e}")

    def load(self):
         return self._app

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def start_in_background(self):
        """
        Start the Gunicorn Master as child process from the main process + run as a daemon
        """
        if self.process is None or not self.process.is_alive():
            self.process = multiprocessing.Process(target=self.run, daemon=True)
            self.process.start()
        else:
            logger.debug("Gunicorn is already running.")

    def stop(self):
        """Stops Gunicorn if it's running."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join()
        else:
            logger.debug("No active Gunicorn process.")

    def _log_master_pid(self, server):
        """
        Log the Gunicorn Master PID. Useful to know as the current process layout looks as follows:
        [Process 1] otto
        For APIs:
        [Process 2 (child of process 1 and is a daemon)] GunicornManager run method
        [Process 3 (child of process 2)] Gunicorn Master
        [Forked from process 2] Gunicorn Worker
        [Forked from process 2] Gunicorn Worker

        For GUI:
        [Process 2 (child process of process 1)] Run streamlit through shell
        [Process 3 (child of process 2)] Streamlit being run through python interpreter

        The GUI workflow will need to be fixed as it is not ideal launching two separate processes to
        run streamlit.
        ....
        """
        logger.info(f"Gunicorn Master started. PID {server.pid}")

    def _log_worker_pid(self, server, worker):
        """
        Log the PID of a worker forked from Gunicorn Master process.
        """
        logger.info(f"Gunicorn Worker started. PID {worker.pid}")
