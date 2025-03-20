import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    network_state: dict
    operations: list[str]
    intent_understanding: str
    network_state: dict
