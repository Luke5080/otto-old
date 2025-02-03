from otto.network_state_db.network_db_operator import NetworkDbOperator
from otto.network_state_db.network_state_finder import NetworkStateFinder

class NetworkState:
    _network_db_operator: NetworkDbOperator
    _nw_state_finder: NetworkStateFinder

    def __init__(self):
        self.current_network_state = {}
        self._network_db_operator = NetworkDbOperator()
        self._nw_state_finder = NetworkStateFinder()

    def get_switch_details(self, switch_id: str) -> dict:
        switch_hex_dpid = f"000000000000000{switch_id}"  # need to write as 16 hex DPID for some RYU API calls

        switch_struct = {
            "name": switch_hex_dpid,
            "ports": self._nw_state_finder.get_ports(switch_hex_dpid),
            "portMappings": self._nw_state_finder.get_port_mappings(switch_hex_dpid),
            "connectedHosts": self._nw_state_finder.get_connected_hosts(switch_hex_dpid),
            "installedFlows": self._nw_state_finder.get_installed_flows(str(switch_id))
        }

        return switch_struct

    def create_network_state(self):
        found_switches = self._nw_state_finder.get_switches()

        for switch in found_switches:
            switch_info = self.get_switch_details(str(switch))

            self.current_network_state[switch] = switch_info

        for _, switch_struct in self.current_network_state.items():
            self._network_db_operator.put_switch_to_db(switch_struct.copy())

    def delete_switch_nw_state(self, switch_dpid: str) -> None:
        del self.current_network_state[switch_dpid]

        self._network_db_operator.remove_switch_document(switch_dpid)

    def add_to_nw_state(self, switch_id: str) -> None:
        switch_info = self.get_switch_details(switch_id)

        self.current_network_state[switch_id] = switch_info

        self._network_db_operator.put_switch_to_db(switch_info)

    def modify_switch_entry(self, switch_id: str, **kwargs) -> None:
        for key, value in kwargs.items():
            self.current_network_state[switch_id][key] = value

        self._network_db_operator.modify_switch_document(switch_id, **kwargs)

    def __repr__(self):
        ...

    def __str__(self):
        ...

    def __getitem__(self, item):
        ...
