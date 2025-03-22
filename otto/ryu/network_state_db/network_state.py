import networkx as nx

from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder


class NetworkState:
    _network_db_operator: NetworkDbOperator
    _nw_state_finder: NetworkStateFinder
    network_graph: nx.Graph

    def __init__(self):
        self._network_db_operator = NetworkDbOperator()
        self._network_db_operator.connect()

        self._nw_state_finder = NetworkStateFinder()

    def get_network_state(self) -> dict:
        found_switches = self._nw_state_finder.get_switches()

        for switch in found_switches:
            switch_info = self._nw_state_finder.get_switch_details(str(switch))
            yield switch_info

    def create_network_state_db(self) -> None:
        for found_switch in self.get_network_state():
            self._network_db_operator.put_switch_to_db(found_switch)

    def get_registered_state(self) -> dict:
        return self._network_db_operator.dump_network_db()

    def __getitem__(self, switch_id: str) -> dict:
        return self._nw_state_finder.get_switch_details(switch_id)
