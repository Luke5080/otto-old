import subprocess
import os

import signal

class StreamlitRunner():
      def __init__(self):
          self._start_command = "python3 -m streamlit run otto/gui/Dashboard.py > /dev/null"
          self.pid = None
          self.process = None


      def start_streamlit(self):
          try:
            self.process = subprocess.Popen(self._start_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
          except Exception as e:
                 raise Exception(f"Could not start Streamlit: {e}")

          self.pid = self.process.pid

      def stop_streamlit(self):
          if self.pid or self.process is not None:
            try:
              os.kill(self.pid, singal.SIGTERM)

            except ProcessLookupError:
                   print("Streamlit is not running")
