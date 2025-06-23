import hashlib
import json

import requests
from requests.exceptions import ConnectionError, HTTPError

from otto.exceptions import (FlowRetrievalException, HostRetrievalException,
                             PortMappingException, PortRetrievalException,
                             SwitchRetrievalException)


class NetworkStateFinder:

    def get_network_state(self) -> dict:
        """
        Method to find the current network state. First obtains a list of current
        switches found in the network and then uses the get_switch_details method
        to create a dictionary for each switch. Each dictionary created for a switch
        is aggregated into one dictionary to represent the current network state.
        Creates a SHA256 Hash of the dictionary to uniquely identify the current
        network state

        Returns:
            dict: dictionary representing the current network state
        """
        found_switches = self.get_switches()

        network_elements, current_nw_state = {}, {}

        for switch in found_switches:
            switch_info = self.get_switch_details(str(switch))

            network_elements[switch_info["name"]] = switch_info

        current_network_state_id = hashlib.sha256(
            json.dumps(network_elements, sort_keys=True).encode('utf-8')).hexdigest()

        current_nw_state[current_network_state_id] = network_elements

        return current_nw_state

    def get_switch_details(self, switch_id: str) -> dict:
        switch_hex_dpid = format(int(switch_id), '016x')  # need to write as 16 hex DPID for some RYU API calls

        switch_struct = {
            "name": switch_hex_dpid,
            "ports": self.get_ports(switch_hex_dpid),
            "portMappings": self.get_port_mappings(switch_hex_dpid),
            "connectedHosts": self.get_connected_hosts(switch_hex_dpid),
            "installedFlows": self.get_installed_flows(switch_id),
            "installedGroups": self.get_installed_groups(switch_id)
        }

        return switch_struct

    @staticmethod
    def get_switches() -> list[int]:
        """
        Method to obtain a list of switches in the current network using
        the /stats/switches Ryu API. Returns a list of each switch's datapath
        e.g. [5,4,1,2]
        """
        try:
            switch_list = requests.get('http://127.0.0.1:8080/stats/switches')
            switch_list.raise_for_status()
        except HTTPError as e:
            raise SwitchRetrievalException(
                f"""
                Error while contacting API /stats/switches.
                Exception raised: {e}
                """
            )

        except ConnectionError as e:
            raise SwitchRetrievalException(
                f"""
                Error while contacting API /stats/switches.
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise SwitchRetrievalException(e)

        return switch_list.json()

    @staticmethod
    def get_ports(switch_dpid: str) -> list:
        """
        Method to return a list of ports for a given switch
        using the /topology/switches/{dpid} Ryu API. Returns
        a dictionary for each port including physical address,
        port number and port name.
        """
        try:
            switch_details = requests.get(f"http://127.0.0.1:8080/v1.0/topology/switches/{switch_dpid}")
            switch_details.raise_for_status()
        except HTTPError as e:
            raise PortRetrievalException(
                f"""
                Error while contacting API /V1.0/topology/switches.
                Exception raised: {e}
                """
            )

        except ConnectionError as e:
            raise PortRetrievalException(
                f"""
                Error while contacting API /V1.0/topology/switches.
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise PortRetrievalException(e)

        if len(switch_details.json()) and 'ports' in switch_details.json()[0]:
            retrieved_switch_ports = switch_details.json()[0]['ports']

            for port in retrieved_switch_ports:
                del port['dpid']  # we don't need to include the dpid in each port desc, so remove it

            return retrieved_switch_ports

        return []

    @staticmethod
    def get_port_mappings(switch_dpid: str) -> dict:
        """
        Method which returns the port mappings for each port on a switch.
        Uses the /topology/links/{dpid} Ryu API and returns a dictionary
        which follows the form src : dst, where src and dst are port names
        e.g. s1-eth1 : s4-eth2
        """
        try:
            links_found = requests.get(f"http://127.0.0.1:8080/v1.0/topology/links/{switch_dpid}")
            links_found.raise_for_status()
        except HTTPError as e:
            raise PortMappingException(
                f"""
                Error while contacting API /v1.0/topology/links.
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise PortMappingException(e)

        switch_port_mapping = {}

        links_found = links_found.json()

        if len(links_found):
            for port_mapping in links_found:
                source_port = port_mapping['src']['name']
                destination = port_mapping['dst']['name']

                switch_port_mapping[source_port] = destination

        return switch_port_mapping

    @staticmethod
    def get_connected_hosts(switch_dpid: str) -> dict:
        try:
            hosts_discovered = requests.get(f"http://127.0.0.1:8080/v1.0/topology/hosts/{switch_dpid}")
            hosts_discovered.raise_for_status()
        except HTTPError as e:
            raise HostRetrievalException(
                f"""
                Error while contacting API /v1.0/topology/hosts.
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise HostRetrievalException(e)

        host_mappings = {}

        hosts_discovered = hosts_discovered.json()

        if hosts_discovered:
            host_count = 1
            for connected_host in hosts_discovered:
                connected_port = connected_host['port']['name']

                host_id = f"host-{str(int(switch_dpid, 16))}-{str(host_count)}"

                host_details = {
                    'id': host_id,
                    'mac': connected_host['mac'],
                    'ipv4': connected_host['ipv4'],
                    'ipv6': connected_host['ipv6']
                }

                host_mappings[connected_port] = host_details

                host_count += 1

        return host_mappings

    @staticmethod
    def get_installed_groups(switch_id: str):
        try:
            installed_groups = requests.get(f"http://127.0.0.1:8080/stats/groupdesc/{switch_id}")
            installed_groups.raise_for_status()
        except HTTPError as e:
            raise HostRetrievalException(
                f"""
                Error while contacting API /stats/groupdesc
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise HostRetrievalException(e)

        installed_groups = installed_groups.json()

        return installed_groups[switch_id]

    @staticmethod
    def get_installed_flows(switch_dpid: str) -> dict:
        try:
            installed_flows_found = requests.get(f"http://127.0.0.1:8080/stats/flow/{switch_dpid}")
            installed_flows_found.raise_for_status()
        except HTTPError as e:
            raise FlowRetrievalException(
                f"""
                Error while contacting API /stats/flows.
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise FlowRetrievalException(e)

        flows_found_dict = installed_flows_found.json()

        formatted_flows = {}

        if len(flows_found_dict):
            switch_key, = flows_found_dict

            for flow in flows_found_dict[switch_key]:
                target_hash_fields = {
                    'priority': flow['priority'],
                    'table_id': flow['table_id'],
                    'match': flow['match'],
                    'actions': flow['actions'],
                    'dpid': switch_dpid
                }

                hash_str = json.dumps(target_hash_fields, sort_keys=True)

                flow_hash = str(hashlib.md5(hash_str.encode('utf-8')).hexdigest())

                del flow["duration_sec"]
                del flow["duration_nsec"]

                formatted_flows[flow_hash] = flow

        return formatted_flows
