from otto.controller_environment import ControllerEnvironment
from otto.ryu.network_state_db.network_state import NetworkState
from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder
from otto.ryu.network_state_db.network_state_updater import NetworkStateUpdater


class RyuEnvironment(ControllerEnvironment):
    network_state = NetworkState()
    network_state_updater = NetworkStateUpdater(network_state)
    network_state_finder = NetworkStateFinder()

    def create_network_state(self):
        self.network_state.create_network_state_db()

    def start_state_updater(self):
        self.network_state_updater.start()

    def stop_state_updater(self):
        self.network_state_updater.stop_event.set()
