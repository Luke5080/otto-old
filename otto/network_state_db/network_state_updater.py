import time
from threading import Thread
from network_state import NetworkState

class NetworkStateUpdater(Thread):
    _nw_state: NetworkState

    def __init__(self):
        super().__init__()
        self._nw_state = NetworkState()

    def run(self):

        while True:
            current_nw_state = [document for document in self._nw_state.get_network_state()]

            if current_nw_state != self._nw_state.get_registered_state():
                raise Exception

            time.sleep(60)