import atexit
import os
import signal
import subprocess

from otto.otto_logger.logger_config import logger


class StreamlitRunner():
    def __init__(self):
        self._start_command = ["python3","-m", "streamlit", "run", "otto/gui/Dashboard.py"]
        self.process = None
        atexit.register(self.stop_streamlit)

    def start_streamlit(self):
        """
        Start Streamlit GUI in background. This method will call subprocess.Popen to create a child process
        which will run otto/gui/Dashboard.py.
        """
        try:
            self.process = subprocess.Popen(self._start_command, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
        except Exception as e:
            raise Exception(f"Could not start Streamlit: {e}")

        logger.info(f"Streamlit process started at {self.process.pid}")

    def stop_streamlit(self):
        """
        Terminate the streamlit process if it exists
        """
        logger.debug("Stopping Gui..")
        if self.process:
            try:
                self.process.terminate()
                self.process.wait()
                logger.debug("OttoGui stopped")
            except ProcessLookupError:
                logger.debug("Streamlit is not running")
