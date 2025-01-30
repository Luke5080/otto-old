import requests
from pymongo import MongoClient

class NetworkStateCreator:
    _MongoConnector: MongoClient

    def __init__(self):
        self._MongoConnector = MongoClient('localhost',27017)

    @staticmethod
    def _get_switches() -> list:
        switch_list = requests.get('http://127.0.0.1:8080/stats/switches')

        return switch_list.json()

    @staticmethod
    def _get_ports(switch_dpid: str) -> dict:
        switch_details = requests.get(f"http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}")

        retrieved_switch_ports = switch_details.json()[0]['ports']

        for port in retrieved_switch_ports:
            del port['dpid'] # we don't need to include the dpid in each port desc, so remove it

        return retrieved_switch_ports

    @staticmethod
    def _get_port_mappings(switch_dpid: str) -> dict:
        links_found = requests.get(f"http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}")

        switch_port_mapping = {}

        for port_mapping in links_found.json():
            source_port = port_mapping['src']['name']
            destination = port_mapping['dst']['name']

            switch_port_mapping[source_port] = destination

        return switch_port_mapping

    @staticmethod
    def _get_connected_hosts(switch_dpid: str) -> dict:
        hosts_discovered = requests.get(f"http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}")

        host_mappings = {}

        for connected_host in hosts_discovered.json():
            connected_port = connected_host['port']['name']

            host_details  = {
                'mac' : connected_host['mac'],
                'ipv4' : connected_host['ipv4'],
                'ipv6' : connected_host['ipv6']
            }

            host_mappings[connected_port] = host_details

        return host_mappings

    @staticmethod
    def _get_installed_flows(switch_dpid: str) -> dict:
        print(switch_dpid)
        installed_flows_found = requests.get(f"http://127.0.0.1:8080/stats/flow/{switch_dpid}")

        return installed_flows_found.json()

    def _put_to_db(self, switch_struct: dict) -> None:
        network_state_db = self._MongoConnector["topology"]

        switch_collection = network_state_db["switches"]

        switch_collection.insert_one(switch_struct)

    def create_network_state_db(self) -> None:
        switches_found = self._get_switches()

        for switch in switches_found:
            switch_hex_dpid = f"000000000000000{switch}" # need to write as 16 hex DPID for some RYU API calls

            switch_struct = {
                "name" : switch_hex_dpid,
                "ports" : self._get_ports(switch_hex_dpid),
                "portMappings" : self._get_port_mappings(switch_hex_dpid),
                "connectedHosts" : self._get_connected_hosts(switch_hex_dpid),
                "installedFlows" : self._get_installed_flows(switch)
            }

            self._put_to_db(switch_struct)
