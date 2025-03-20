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
        self.network_graph = nx.Graph()
        self.switch_port_mappings = {}
        self.host_mappings = {}

    def construct_network_graph(self, network_state: dict):
        """
        Create Network Graph and populate switch port mappings so that they can be used
        by the get_path_between_nodes tool.
        """

        # clear the graph, switch port mappings and host mappings each this method is run
        self.network_graph.clear()
        self.switch_port_mappings.clear()
        self.host_mappings.clear()

        for switch, switch_data in network_state.items():
            for switch_port, remote_port in switch_data.get('portMappings', {}).items():
                remote_switch = format(int(remote_port.split('-')[0][1]), '016x')
                self.network_graph.add_edge(switch, remote_switch, port_info=(switch_port, remote_port))

                self.switch_port_mappings[(switch, remote_switch)] = (switch_port, remote_port)
                self.switch_port_mappings[(remote_switch, switch)] = (remote_port, switch_port)

            for switch_port, remote_host in switch_data.get('connectedHosts', {}).items():
                host_id = remote_host['id']
                self.network_graph.add_edge(switch, host_id)

                self.switch_port_mappings[(switch, host_id)] = (switch_port, host_id)
                self.switch_port_mappings[(host_id, switch)] = (host_id, switch_port)

                self.host_mappings.setdefault(switch, {})[switch_port] = host_id

    def get_network_state(self) -> dict:
        found_switches = self._nw_state_finder.get_switches()

        for switch in found_switches:
            switch_info = self._nw_state_finder.get_switch_details(str(switch))
            yield switch_info

    def create_network_state_db(self) -> None:
        for found_switch in self.get_network_state():
            self._network_db_operator.put_switch_to_db(found_switch)

        self.construct_network_graph(self.get_registered_state())

    def get_registered_state(self) -> dict:
        return self._network_db_operator.dump_network_db()


    def __getitem__(self, switch_id: str) -> dict:
        return self._nw_state_finder.get_switch_details(switch_id)
