import subprocess
import os
import atexit
import signal
from otto.otto_logger.logger_config import logger

class StreamlitRunner():
      def __init__(self):
          self._start_command = "python3 -m streamlit run otto/gui/Dashboard.py > /dev/null"
          self.pid = None
          self.process = None
          atexit.register(self.stop_streamlit)

      def start_streamlit(self):
          try:
            self.process = subprocess.Popen(self._start_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
          except Exception as e:
                 raise Exception(f"Could not start Streamlit: {e}")

          self.pid = self.process.pid
          logger.info(f"Streamlit process started at {self.process.pid}")

      def stop_streamlit(self):
          if self.pid or self.process is not None:
            try:
              os.kill(self.pid, signal.SIGTERM)

            except ProcessLookupError:
                   print("Streamlit is not running")
