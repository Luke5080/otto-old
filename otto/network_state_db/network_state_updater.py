import time
from threading import Thread
from otto.network_state_db.network_state import NetworkState
from otto.network_state_db.network_db_operator import NetworkDbOperator
from deepdiff import DeepDiff

class NetworkStateUpdater(Thread):
    _nw_state: NetworkState

    def __init__(self):
        super().__init__()
        self._nw_state = NetworkState()

   def update_value(change: dict) -> None:
       ...

    def run(self):
        while True:
            print("Starting..")
            current_nw_state = {}
            for document in self._nw_state.get_network_state():
                current_nw_state[document["name"]] = document

            diff_found = DeepDiff(self._nw_state.get_registered_state(),current_nw_state)

            if len(diff_found) > 0:
                print(diff_found)

            time.sleep(60)
