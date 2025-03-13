import networkx as nx
import requests
from langchain_core.tools import tool

from otto.ryu.network_state_db.network_state import NetworkState


@tool
def get_nw_state() -> dict:
    """
    Function to get the current entire network state
    """
    network_state = NetworkState.get_instance()
    return network_state.get_registered_state()


@tool
def check_switch(switch_id: str) -> dict:
    """
    Function to check the current configuration of a current switch.
    Args:
        switch_id: ID of the switch (in decimal)
    """
    network_state = NetworkState.get_instance()
    return network_state[switch_id]


@tool
def get_path_between_nodes(source: str, destination: str) -> list[tuple[str, str]]:
    """
    Function to get a path between nodes in the network. The nodes can either be a switch or a host.
    Args:
        source: source of the path to retrieve. source can either be a switch or a host.
        A switch is identified by a 16 HEX switch DPID, e.g. for switch with an ID of decimal = 0000000000000001. 
        For hosts, provide the name of the host e.g. host2.
        destination: destination node for the path. Follow the same format as instructed
        in the source argument descriptor.
    When used to get path between two hosts, the function will return an array of tuples
    indicating the paths through the network device's ports to arrive to the destination. E.g:
    src: host1 destination: host3
    Output:
    [('host1', 's1-eth1'), ('s1-eth3', 's5-eth1'), ('s5-eth3', 's3-eth1'), ('s3-eth3', 'host3')]
    Host1 is connected to switch1 on port 1 (eth1)
    Switch1 port 3 (eth3) is connected to switch5 port 1 (eth1)
    Switch5 port 3 (eth3) is connected to switch3 port 1 (eth1)
    Switch3 is connected to host3 via port 3 (eth3)
    """
    network_state = NetworkState.get_instance()

    shortest_path = nx.shortest_path(network_state.network_graph, source, destination)

    full_path = []
    for i in range(len(shortest_path) - 1):
        full_path.append(network_state.switch_port_mappings[(shortest_path[i], shortest_path[i + 1])])

    return full_path


@tool
def add_rule(switch_id: str, table_id: int, match: dict, actions: list, priority: int = 32768) -> int:
    """
    Function to add an OpenFlow rule to a switch.
    Args:
        switch_id: ID of the switch (in decimal)
        table_id: ID of the table which the flow must be added to
        match: dictionary of match criteria for the flow
        actions: list of actions to be performed for the matching flow
        priority: the priority for the given flow

    Inside the match argument dictionary, include the following keys:
    dl_type, nw_src, tnw_dst, nw_proto and the tp_dst. "actions" is a list of actions to be
    done if the flow criteria is matched. For the action to drop packets, this
    should be an empty list, but if it is to output on a port, use the format:
    "actions":[{"type":"OUTPUT", "port": 2}]
    """

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "dpid": switch_id,
        "cookie": 0,
        "table_id": table_id,
        "priority": priority,
        "match": match,
        "actions": actions
    }

    resp = requests.post('http://localhost:8080/stats/flowentry/add', headers=headers, json=data)

    return resp.status_code


@tool
def delete_rule_strict(switch_id: str, table_id: int, match: dict, actions: list, priority: int) -> int:
    """
    Function to remove a specific OpenFlow rule on a switch.
    Args:
        switch_id: ID of the switch (in decimal)
        table_id: ID of the table which the flow resides on
        match: the match criteria of the specific flow
        actions: list of actions which the flow contains
        priority: the priority for the given flow

    Inside the match argument dictionary, include the following keys:
    dl_type, nw_src, tnw_dst, nw_proto and the tp_dst. All the arguments provided
    to this function must be EXACT matches for the target flow to be deleted from
    the switch.
    """

    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "dpid": switch_id,
        "cookie": 0,
        "table_id": table_id,
        "priority": priority,
        "match": match,
        "actions": actions
    }

    resp = requests.post('http://localhost:8080/stats/flowentry/delete_strict', headers=headers, json=data)

    return resp.status_code


@tool
def modify_rule_strict(switch_id: str, table_id: int, match: dict, actions: list, priority: int) -> int:
    """
    Function to modify a specific OpenFlow rule on a switch.
    Args:
        switch_id: ID of the switch (in decimal)
        table_id: ID of the table where the flow will/is resides on
        match: dictionary of match criteria for the flow
        actions: list of actions to be performed for the matching flow
        priority: the priority for the given flow

    Inside the match argument dictionary, include the following keys:
    dl_type, nw_src, tnw_dst, nw_proto and the tp_dst. "actions" is a list of actions to be
    done if the flow criteria is matched. For the action to drop packets, this
    should be an empty list, but if it is to output on a port, use the format:
    "actions":[{"type":"OUTPUT", "port": 2}]
    """
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "dpid": switch_id,
        "cookie": 0,
        "table_id": table_id,
        "priority": priority,
        "match": match,
        "actions": actions
    }

    resp = requests.post('http://localhost:8080/stats/flowentry/modify_strict', headers=headers, json=data)

    return resp.status_code


@tool
def modify_all_matching_rules(switch_id: str, table_id: int, match: dict, actions: list, priority: int) -> int:
    """
    Function to modify all matching rules based on the inputted arguments on a switch.
    Args:
        switch_id: ID of the switch (in decimal)
        table_id: ID of the table where the flow will/is resides on
        match: dictionary of match criteria for the flow
        actions: list of actions to be performed for the matching flow
        priority: the priority for the given flow

    Inside the match argument dictionary, include the following keys:
    dl_type, nw_src, tnw_dst, nw_proto and the tp_dst. "actions" is a list of actions to be
    done if the flow criteria is matched. For the action to drop packets, this
    should be an empty list, but if it is to output on a port, use the format:
    "actions":[{"type":"OUTPUT", "port": 2}]
    """
    headers = {
        'Content-Type': 'application/json'
    }

    data = {
        "dpid": switch_id,
        "cookie": 0,
        "table_id": table_id,
        "priority": priority,
        "match": match,
        "actions": actions
    }

    resp = requests.post('http://localhost:8080/stats/flowentry/modify_strict', headers=headers, json=data)

    return resp.status_code


def create_tool_list(extra_funcs=None) -> list:
    return [get_nw_state, add_rule, delete_rule_strict,
            modify_rule_strict, modify_all_matching_rules,
            check_switch, get_path_between_nodes]
