from typing import Annotated, TypedDict
import operator
from langchain_core.messages import AnyMessage

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    operations: list[str]
    intent_understanding: str