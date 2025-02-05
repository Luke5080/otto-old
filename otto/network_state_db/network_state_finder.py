import uuid
import requests
from requests.exceptions import HTTPError
from exceptions import (
    SwitchRetrievalException, PortRetrievalException,
    PortMappingException, FlowRetrievalException,
    HostRetrievalException
)

class NetworkStateFinder:

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
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise SwitchRetrievalException(e)

        return switch_list.json()

    @staticmethod
    def get_ports(switch_dpid: str) -> dict:
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
                Please ensure you run Ryu with the following applications:\n
                ryu-manager ryu.app.ofctl_rest ryu.app.rest_topology --observe-links
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise PortRetrievalException(e)

        if len(switch_details.json()) > 0 and 'ports' in switch_details.json()[0]:
            retrieved_switch_ports = switch_details.json()[0]['ports']

            for port in retrieved_switch_ports:
                del port['dpid'] # we don't need to include the dpid in each port desc, so remove it

            return retrieved_switch_ports

        return {}

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

        if len(links_found.json()) > 0:
            for port_mapping in links_found.json():
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

        if len(hosts_discovered.json()) > 0:
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
    def get_installed_flows(switch_dpid: str, create_db=False, compare=False) -> dict:
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

        if create_db:
           formatted_flows = {}

           flows_found_dict = installed_flows_found.json()
        
           switch_key, = flows_found_dict
        
           for flow in flows_found_dict[switch_key]:
               formatted_flows[str(uuid.uuid4())] = flow
            
           return formatted_flows

