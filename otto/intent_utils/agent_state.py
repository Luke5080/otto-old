import operator
from typing import Annotated, TypedDict

import networkx as nx
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

    network_state: dict
    switch_port_mappings: dict
    host_mappings: dict
    network_graph: nx.Graph

    operations: list[str]
    intent_understanding: str
