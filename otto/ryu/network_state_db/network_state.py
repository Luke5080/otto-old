from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder
import networkx as nx
from exceptions import MultipleNetworkStateInstances


class NetworkState:
    _network_db_operator: NetworkDbOperator
    _nw_state_finder: NetworkStateFinder
    network_graph: nx.Graph

    __instance: None

    @staticmethod
    def get_instance():
        if NetworkState.__instance is None:
            NetworkState()
        return NetworkState.__instance

    def __init__(self):
        if self.__instance is None:
            self._network_db_operator = NetworkDbOperator.get_instance()
            self._nw_state_finder = NetworkStateFinder()
            self.network_graph = nx.Graph()
            self.switch_port_mappings = {}

        else:
            raise MultipleNetworkStateInstances(f"An occurrence of Network State already exists at {self.__instance}")

    def get_switch_details(self, switch_id: str) -> dict:
        switch_hex_dpid = format(int(switch_id), '016x')  # need to write as 16 hex DPID for some RYU API calls

        switch_struct = {
            "name": switch_hex_dpid,
            "ports": self._nw_state_finder.get_ports(switch_hex_dpid),
            "portMappings": self._nw_state_finder.get_port_mappings(switch_hex_dpid),
            "connectedHosts": self._nw_state_finder.get_connected_hosts(switch_hex_dpid),
            "installedFlows": self._nw_state_finder.get_installed_flows(switch_id)
        }

        return switch_struct

    def construct_network_graph(self, network_state: dict):
        """
        Create Network Graph and populate switch port mappings so that they can be used
        by the get_path_between_nodes tool.
        """
        self.network_graph.clear()
        self.switch_port_mappings = {}

        host_id = 1  # this is not great
        for switch, switch_data in network_state.items():
            for switch_port, remote_port in switch_data.get('portMappings', {}).items():
                remote_switch = format(int(remote_port.split('-')[0][1]), '016x')
                self.network_graph.add_edge(switch, remote_switch, port_info=(switch_port, remote_port))

                self.switch_port_mappings[(switch, remote_switch)] = (switch_port, remote_port)
                self.switch_port_mappings[(remote_switch, switch)] = (remote_port, switch_port)

            for switch_port, remote_host in switch_data.get('connectedHosts', {}).items():
                host_string = f"host{host_id}"
                self.network_graph.add_edge(switch, host_string)

                self.switch_port_mappings[(switch, host_string)] = (switch_port, host_string)
                self.switch_port_mappings[(switch, host_string)] = (switch_port, host_string)

                host_id += 1

    def get_network_state(self) -> dict:
        found_switches = self._nw_state_finder.get_switches()

        for switch in found_switches:
            switch_info = self.get_switch_details(str(switch))
            yield switch_info

    def create_network_state_db(self) -> None:
        for found_switch in self.get_network_state():
            self._network_db_operator.put_switch_to_db(found_switch)

    def delete_switch_nw_state(self, switch_dpid: str) -> None:
        self._network_db_operator.remove_switch_document(switch_dpid)

    def add_to_nw_state(self, switch_dpid: str) -> None:
        switch_info = self.get_switch_details(switch_dpid)

        self._network_db_operator.put_switch_to_db(switch_info)

    def modify_switch_entry(self, switch_dpid: str, **kwargs) -> None:
        self._network_db_operator.modify_switch_document(switch_dpid, **kwargs)

    def get_registered_state(self) -> dict:
        return self._network_db_operator.dump_network_db()

    def __repr__(self):
        ...

    def __str__(self):
        ...

    def __getitem__(self, switch_id: str) -> dict:
        return self.get_switch_details(switch_id)
