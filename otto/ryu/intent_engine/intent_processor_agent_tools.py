import requests
from langchain_core.tools import tool, StructuredTool
from otto.ryu.network_state_db.network_state import NetworkState


@tool
def get_nw_state() -> dict:
    """
    Function to get the current entire network state
    """
    network_state = NetworkState()
    return network_state.get_registered_state()


@tool
def check_switch(switch_id: str) -> dict:
    """
    Function to check the current configuration of a current switch.
    Args:
        switch_id: ID of the switch (in decimal)
    """
    network_state = NetworkState()
    return network_state[switch_id]


@tool
def add_rule(switch_id: str, table_id: int, match: dict, actions: list, priority: int = 0) -> int:
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
def delete_rule(switch_id: str, table_id: int, match: dict, actions: list, priority: int) -> int:
    """
    Function to remove an OpenFlow rule to a switch.
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

    resp = requests.post('http://localhost:8080/stats/flowentry/delete_strict', headers=headers, json=data)

    return resp.status_code


def create_tool_list(extra_funcs=None) -> list:
    return [get_nw_state, add_rule, delete_rule, check_switch]
