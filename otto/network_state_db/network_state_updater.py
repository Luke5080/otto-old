from network_state_finder import NetworkStateFinder
from network_state import NetworkState

class NetworkStateUpdater:
    _nw_state_finder: NetworkStateFinder

    def __init__(self):
        self._nw_state_finder = NetworkStateFinder()
        self.nw_state = NetworkState()

    def get_nw_state(self):
        found_switches = self._nw_state_finder.get_switches()

        found_nw_state = {}

        for switch in found_switches:
            switch_details = self.nw_state.get_switch_details(str(switch))

            found_nw_state[switch] = switch_details

        return found_nw_state


    def compare_nw_state(self):

        found_nw_state = self.get_nw_state()

        if found_nw_state != self.nw_state.current_network_state:
            pass

