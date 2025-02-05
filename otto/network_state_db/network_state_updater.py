import time
from threading import Thread
from otto.network_state_db.network_state import NetworkState
from deepdiff import DeepDiff

class NetworkStateUpdater(Thread):
    _nw_state: NetworkState

    def __init__(self):
        super().__init__()
        self._nw_state = NetworkState()

    def run(self):

        while True:
            print("Starting..")
            current_nw_state = {}
            for document in self._nw_state.get_network_state():
                current_nw_state[document["name"]] = document

            # do not need these for now, and these will trigger an update each time this loop runs
            # not ideal at this point in time. just grab important info.
            excluded_keys = [
               r"root\['[^']+'\]\['installedFlows'\]\['[^']+'\]\['duration_nsec'\]",
               r"root\['[^']+'\]\['installedFlows'\]\['[^']+'\]\['duration_sec'\]"
            ]

            # diff_found = DeepDiff(self._nw_state.get_registered_state(),current_nw_state,exclude_regex_paths=excluded_keys)

            old = self._nw_state.get_registered_state()
            # print(old['0000000000000001'])
            print("/n")
            # print(current_nw_state['0000000000000001'])
            """
            if len(diff_found) > 0:
                print(diff_found)
            """
            time.sleep(60)
