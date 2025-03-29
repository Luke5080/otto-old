import atexit
import os
import signal
import subprocess

from otto.otto_logger.logger_config import logger


class StreamlitRunner():
    def __init__(self):
        self._start_command = "python3 -m streamlit run otto/gui/Dashboard.py > /dev/null"
        self.pid = None
        self.process = None
        atexit.register(self.stop_streamlit)

    def start_streamlit(self):
        """
        Start Streamlit GUI in background. This method will call subprocess.Popen to create a child process
        which will run otto/gui/Dashboard.py. As it needs to be run through the Python interpreter, this child
        process will call a new process to run it through the Python interpreter.
        """
        try:
            self.process = subprocess.Popen(self._start_command, shell=True, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
        except Exception as e:
            raise Exception(f"Could not start Streamlit: {e}")

        self.pid = self.process.pid
        logger.info(f"Streamlit process started at {self.process.pid}")

    def stop_streamlit(self):
        """
        Stop the streamlit process if it exists by sending SIGTERM to running process
        """
        logger.debug("Stopping OttoShell..")
        if self.pid or self.process is not None:
            try:
                os.kill(self.pid, signal.SIGTERM)
                logger.debug("OttoShell stopped")
            except ProcessLookupError:
                logger.debug("Streamlit is not running")
