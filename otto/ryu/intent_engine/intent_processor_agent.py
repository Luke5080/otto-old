import uuid
from typing import Union, Optional

import networkx as nx
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import SystemMessage, merge_message_runs
from langchain_openai.chat_models.base import BaseChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from otto.intent_utils.agent_state import AgentState
from otto.intent_utils.model_factory import ModelFactory
from otto.ryu.network_state_db.network_state_broker import NetworkStateBroker
from otto.ryu.network_state_db.processed_intents_db_operator import ProcessedIntentsDbOperator


class IntentProcessor:
    def __init__(self, model: Union[BaseChatOpenAI, BaseChatModel],
                 tools: list, system_prompt: str,
                 context: Optional[str] = "User"):

        self.context = context
        self.system = system_prompt
        self.tool_list = tools

        self.tool_node = ToolNode(self.tool_list)
        self.tools = {tool.name: tool for tool in tools}

        self.model = model.bind_tools(tools, tool_choice="auto")
        self.model_name = model.model_name if not isinstance(model,
                                                             ChatAnthropic) else model.model  # silly ChatAnthropic shenanigans

        self.model_factory = ModelFactory()

        self.processed_intents_db_conn = ProcessedIntentsDbOperator()
        self.network_state_broker = NetworkStateBroker()

        graph = StateGraph(AgentState)

        graph.add_node("construct_network_state", self.construct_network_state)
        graph.add_node("reason_intent", self.reason_intent)
        graph.add_node("execute_action", self.tool_node)
        graph.add_node("save_intent", self.save_intent)

        graph.set_entry_point("construct_network_state")
        graph.add_edge("construct_network_state", "reason_intent")
        graph.add_conditional_edges(
            "reason_intent",
            self.needs_action,
            {"continue": "execute_action", "done": "save_intent"}
        )

        graph.add_edge("execute_action", "reason_intent")
        graph.add_edge("save_intent", END)

        self.graph = graph.compile()

    def construct_network_state(self, state: AgentState):
        """
        Method to construct the network state to be used by a single agent during an intent fulfilment operation.
        This is entrypoint to the graph, and constructs three important items to be added to the agent's state:
            network_state: full dictionary of documents registered in otto_network_state_db
            network_graph: links between hosts and switches modelled in a nx.Graph object
            switch_port_mappings: dictionary which follows the structure: {(s1, s2): (s1-eth1: s2-eth2)}
            which describes the interfaces used to connect two nodes.

        The network_state will be used as a reference to the agent as to how the current network looks,
        and network_graph and switch_port_mappings is utilised in the get_path_between_nodes tool to find a path
        between two nodes in the network.
        """

        agent_run_id = str(uuid.uuid4())

        network_state = self.network_state_broker.provide_network_state(agent_run_id)

        network_graph = nx.Graph()

        switch_port_mappings = {}

        state_id = next(iter(network_state), None)

        for switch, switch_data in network_state[state_id].items():
            for switch_port, remote_port in switch_data.get('portMappings', {}).items():
                remote_switch = format(int(remote_port.split('-')[0][1]), '016x')
                network_graph.add_edge(switch, remote_switch, port_info=(switch_port, remote_port))

                switch_port_mappings[(switch, remote_switch)] = (switch_port, remote_port)
                switch_port_mappings[(remote_switch, switch)] = (remote_port, switch_port)

            for switch_port, remote_host in switch_data.get('connectedHosts', {}).items():
                host_id = remote_host['id']
                network_graph.add_edge(switch, host_id)

                switch_port_mappings[(switch, host_id)] = (switch_port, host_id)
                switch_port_mappings[(host_id, switch)] = (host_id, switch_port)
        return {
            'agent_run_id': agent_run_id,
            'network_state': network_state,
            'network_graph': network_graph,
            'switch_port_mappings': switch_port_mappings
        }

    def reason_intent(self, state: AgentState):
        """LLM decides next action based on intent and state"""

        messages = state['messages']

        # need to reformat this way so that ChatAnthropic doesn't complain..
        messages = [SystemMessage(content=self.system)] + [
            SystemMessage(content=f"Current Network State:\n{state['network_state']}")] + messages

        messages = merge_message_runs(messages)

        response = self.model.invoke(messages)

        return {'messages': [response]}

    def needs_action(self, state: AgentState):
        """Check if any actions are needed"""
        last_msg = state['messages'][-1]

        return "continue" if len(last_msg.tool_calls) > 0 else "done"

    def save_intent(self, state: AgentState):
        """ Register processed intent into processed_intents_db
        operations = []
        for message in state['messages']:
            if isinstance(message, AIMessage) and len(message.tool_calls) > 0:
                for tool in message.tool_calls:
                    operations.append(f"{tool['name']}({tool['args']})")

        self.processed_intents_db_conn.connect()

        processed_intent = self.processed_intents_db_conn.save_intent(context=self.context,
                                                                      intent=state['messages'][0].content,
                                                                      operations=operations,
                                                                      timestamp=datetime.now())

        self.processed_intents_db_conn.register_model_usage(self.model_name)

        return {'save_intent': processed_intent, 'operations': operations}
        """
        self.network_state_broker.terminate_agent_run(state['agent_run_id'])

    def change_model(self, model):
        """Change the language model used by IntentProcessor"""
        chosen_model = self.model_factory.get_model(model)
        self.model = chosen_model.bind_tools(self.tool_list, tool_choice="auto")
