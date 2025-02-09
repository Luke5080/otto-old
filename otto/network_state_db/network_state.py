from otto.network_state_db.network_db_operator import NetworkDbOperator
from otto.network_state_db.network_state_finder import NetworkStateFinder
from pymongo import InsertOne

class NetworkState:
    _network_db_operator: NetworkDbOperator
    _nw_state_finder: NetworkStateFinder

    def __init__(self):
        self._network_db_operator = NetworkDbOperator.get_instance()
        self._nw_state_finder = NetworkStateFinder()
        self._flow_mapping = {}

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

    def get_registered_state(self) -> list[dict]:
        return self._network_db_operator.dump_network_db()

    def __repr__(self):
        ...

    def __str__(self):
        ...

    def __getitem__(self, switch_dpid: str) -> dict:
        return self._network_db_operator.get_switch_document(switch_dpid)
