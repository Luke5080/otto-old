from typing import Annotated

import networkx as nx
import requests
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder


@tool
def check_switch(switch_id: str) -> dict:
    """
    Function to check the current configuration of a current switch.
    Args:
        switch_id: ID of the switch (in decimal)
    """

    nw_state_finder = NetworkStateFinder()
    return nw_state_finder.get_switch_details(switch_id)


@tool
def get_path_between_nodes(source: str,
                           destination: str,
                           network_graph: Annotated[nx.Graph, InjectedState("network_graph")],
                           switch_port_mappings: Annotated[dict, InjectedState("switch_port_mappings")],
                           ) -> list[tuple[str, str]]:
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

    shortest_path = nx.shortest_path(network_graph, source, destination)

    full_path = []

    for i in range(len(shortest_path) - 1):
        full_path.append(switch_port_mappings[(shortest_path[i], shortest_path[i + 1])])

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
def modify_all_matching_rules(switch_id: str, table_id: int, match: dict,
                              actions: list, priority: int) -> int:
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

@tool
def add_group_entry(switch_id: int, bucket_type: str, group_id: int,
                    buckets: list[dict]) -> int:
    """
    Function to add an OpenFlow group to a switch.
    Args:
        switch_id: ID of the switch (in decimal)
        bucket_type: Can either be one of the four options: SELECT, ALL, INDIRECT and FAST-FAILOVER.
        SELECT: In a SELECT group, each bucket in the group has an assigned weight.
        Each packet that enters the group is sent to a single bucket. The bucket selection algorithm
        is undefined and is dependent on the switch’s implementation; however, weighted round robin is perhaps
        the most obvious and simplest choice of packet distribution to buckets. The weight of a bucket is provided as a
        special parameter to each bucket. Each bucket in a SELECT group is still a list of actions, so any actions
        supported by OpenFlow can be used in each bucket, and like the ALL group, the buckets need not be uniform.

        ALL: Will take any packet received as input and duplicate it to be operated on independently by each bucket
        in the bucket list. In this way, an ALL group can be used to replicate and then operate on separate copies of the packet
        defined by the actions in each bucket. Different and distinct actions can be in each bucket,
        which allows different operations to be performed on different copies of the packet.

        INDIRECT: contains only a single bucket where all packets received by the group are sent to this lone bucket.
        In other words, the INDIRECT group does not contain a list of buckets but a single bucket (or single list of actions) instead.
        The purpose of the INDIRECT group is to encapsulate a common set of actions used by many flows. For example, if flows A, B, and C match on different packet headers but have a common set or subset of actions,
        these flows can send packets to the single INDIRECT group as opposed to having to duplicate the list of common actions for each flow.

        group_id: ID for the given group.
        buckets: List of buckets for the group, where each bucket is defined in a dictionary. Each bucket should
        have an "actions" key, which holds a dictionary for the action. For example, {"type": "OUTPUT", "port": 1}
        For a SELECT group for load balancing, a "weight" key should be added to the bucket dictionary, e.g:
         [
            {
                "weight": 100,
                "actions": [
                    {
                        "type": "OUTPUT",
                        "port": 1
                    }
                ]
            }, ....
        ]
    """

    # definitions for the OpenFlow groups taken from:
    # https://floodlight.atlassian.net/wiki/spaces/floodlightcontroller/pages/7995427/How+to+Work+with+Fast-Failover+OpenFlow+Groups
    headers = {
        'Content-Type': 'application/json'
    }

    data = {

        "dpid": switch_id,
        "type": bucket_type,
        "group_id": group_id,
        "buckets": buckets
    }

    resp = requests.post("http://localhost:8080/stats/groupentry/add", headers=headers, json=data)

    return resp.status_code


def create_tool_list(extra_funcs=None) -> list:
    return [add_rule, delete_rule_strict,
            modify_rule_strict, modify_all_matching_rules,
            check_switch, get_path_between_nodes, add_group_entry]
