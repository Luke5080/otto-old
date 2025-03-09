from datetime import datetime
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from exceptions import ProcessedIntentsDbException
from otto.intent_utils.agent_state import AgentState
from otto.intent_utils.model_factory import ModelFactory


class IntentProcessor:
    def __init__(self, model, tools, system_prompt, context):
        self.context = context
        self.mongo_connector = MongoClient('localhost', 27018)
        self.database = self.mongo_connector['intent_history']
        self.collection = self.database['processed_intents']
        self.system = system_prompt
        self.tool_list = tools
        self.tools = {tool.name: tool for tool in tools}
        self.model = model.bind_tools(tools, tool_choice="auto")
        self.model_factory = ModelFactory()

        graph = StateGraph(AgentState)
        graph.add_node("understand_intent", self.understand_intent)
        graph.add_node("check_state", self.check_state)
        graph.add_node("reason_intent", self.reason_intent)
        graph.add_node("execute_action", self.execute_action)
        graph.add_node("save_intent", self.save_intent)

        graph.set_entry_point("understand_intent")
        graph.add_edge("understand_intent", "check_state")
        graph.add_edge("check_state", "reason_intent")
        graph.add_conditional_edges(
            "reason_intent",
            self.needs_action,
            {"continue": "execute_action", "done": "save_intent"}
        )

        graph.add_edge("execute_action", "reason_intent")
        graph.add_edge("save_intent", END)

        self.graph = graph.compile()

    def change_model(self, model):
        """Change the language model used by IntentProcessor"""
        chosen_model = self.model_factory.get_model(model)
        self.model = chosen_model.bind_tools(self.tool_list, tool_choice="auto")

    def save_intent(self, state: AgentState):
        """ Register processed intent into processed_intents_db"""

        try:
            processed_intent = {
                "declaredBy": self.context,
                "intent": state['messages'][0].content,
                "outcome": state.get('operations', {}),
                "timestamp": str(datetime.now())
            }

            self.collection.insert_one(processed_intent)

        except PyMongoError as e:
            raise ProcessedIntentsDbException(
                f"Error while putting processed_intent into otto_processed_intents_db: {e}")
        return {'save_intent': processed_intent}

    def check_state(self, state: AgentState):
        """Get current network state"""
        current_state = self.tools["get_nw_state"].invoke({})
        return {
            'messages': [
                SystemMessage(content=f"Current Network State:\n{current_state}")
            ],
            'network_state': current_state
        }

    def understand_intent(self, state: AgentState):
        messages = state['messages']

        messages = [SystemMessage(
            content="Clearly provide your full understanding of the intent. This should be reasoned in depth, and should be an individual task, meaning you can not get help from a human operator.\n")] + messages

        response = self.model.invoke(messages)

        return {'messages': state['messages'], 'intent_understanding': response}

    def reason_intent(self, state: AgentState):
        """LLM decides next action based on intent and state"""
        messages = state['messages']

        messages = [SystemMessage(content=self.system)] + messages

        response = self.model.invoke(messages)

        return {'messages': [response]}

    def needs_action(self, state: AgentState):
        """Check if any actions are needed"""
        last_msg = state['messages'][-1]
        print(last_msg)
        return "continue" if len(last_msg.tool_calls) > 0 else "done"

    def execute_action(self, state: AgentState):
        """Execute network configuration tools"""
        tool_calls = state['messages'][-1].tool_calls
        results = []

        operations = state.get('operations', [])
        for t in tool_calls:
            try:
                tool = self.tools.get(t['name'])
                result = tool.invoke(t['args']) if tool else "Invalid tool"
                results.append(ToolMessage(
                    tool_call_id=t['id'],
                    name=t['name'],
                    content=str(result)
                ))

                operations.append(t['name'])

            except Exception as e:
                results.append(ToolMessage(
                    tool_call_id=t['id'],
                    name=t['name'],
                    content=f"Error: {str(e)}"
                ))

        return {'messages': results, 'operations': operations}
