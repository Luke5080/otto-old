"""
    def put_switch_to_db(self, switch_struct: dict) -> None:
        network_state_db = self._MongoConnector["topology"]

        switch_collection = network_state_db["switches"]

        try:
            switch_collection.insert_one(switch_struct)
        except Exception as e:
            raise NetworkDatabaseException(e)

    def create_network_state(self, switches: list[int]) -> None:
        for switch in switches:
            switch_hex_dpid = f"000000000000000{switch}" # need to write as 16 hex DPID for some RYU API calls

            switch_struct = {
                "name": switch_hex_dpid,
                "ports": self._get_ports(switch_hex_dpid),
                "portMappings": self._get_port_mappings(switch_hex_dpid),
                "connectedHosts": self._get_connected_hosts(switch_hex_dpid),
                "installedFlows": self._get_installed_flows(str(switch))
            }

            self._current_network_state[switch_hex_dpid] = switch_struct

    def create_network_state_db(self) -> None:
        switches_found = self._get_switches()

        self.create_network_state(switches_found)

        for switch_struct in self._current_network_state:
            self.put_to_db(switch_struct)
"""