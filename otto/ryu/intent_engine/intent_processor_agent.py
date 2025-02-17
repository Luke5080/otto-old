from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from otto.ryu.intent_engine.agent_state import AgentState

class IntentProcessor:
    def __init__(self, model, tools, system_prompt):
        self.system = system_prompt
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools, tool_choice="auto")

        graph = StateGraph(AgentState)
        graph.add_node("check_state", self.check_state)
        graph.add_node("reason_intent", self.reason_intent)
        graph.add_node("execute_action", self.execute_action)
        # graph.add_node("check_element", self.check_element)

        graph.set_entry_point("check_state")
        graph.add_edge("check_state", "reason_intent")
        graph.add_conditional_edges(
            "reason_intent",
            self.needs_action,
            {"continue": "execute_action", "done": END}
        )

        graph.add_edge("execute_action", "check_state")

        self.graph = graph.compile()

    """
    def check_element(self, state: AgentState, switch_id:str):
        Get details of a switch
        Args:
            switch_id: switch id in decimal


        switch_document = self.tools["check_switch"].invoke({"switch_id": switch_id})

        return {
            'messages': [
                SystemMessage(content=f"Switch document {switch_id}:\n{switch_document}")
            ]
        }
    """

    def check_state(self, state: AgentState):
        """Get current network state"""
        current_state = self.tools["get_nw_state"].invoke({})
        return {
            'messages': [
                SystemMessage(content=f"Current Network State:\n{current_state}")
            ]
        }

    def reason_intent(self, state: AgentState):
        """LLM decides next action based on intent and state"""
        messages = state['messages']

        messages = [SystemMessage(content=self.system)] + messages

        response = self.model.invoke(messages)

        return {'messages': [response]}

    def needs_action(self, state: AgentState):
        """Check if any actions are needed"""
        last_msg = state['messages'][-1]
        return "continue" if len(getattr(last_msg, 'tool_calls', [])) > 0 else "done"

    def execute_action(self, state: AgentState):
        """Execute network configuration tools"""
        tool_calls = state['messages'][-1].tool_calls
        results = []

        for t in tool_calls:
            try:
                tool = self.tools.get(t['name'])
                result = tool.invoke(t['args']) if tool else "Invalid tool"
                results.append(ToolMessage(
                    tool_call_id=t['id'],
                    name=t['name'],
                    content=str(result)
                ))
            except Exception as e:
                results.append(ToolMessage(
                    tool_call_id=t['id'],
                    name=t['name'],
                    content=f"Error: {str(e)}"
                ))

        return {'messages': results}


prompt = """
    You are one assistant as part of a team of network assistants who work together to help fulfill a given intent where the intent only
    provides the business goal and deliverable to achieve, without specifying how to do it. As part of this team of assistants who help
    to turn intents into actions which should be performed in the network to fulfill the given intent, your main responsibility is to
    operate the tools which modify the underlying network to achieve the goals set out by the intent. Out of the team, you are
    "Modify Network Operator", where you are the only assistant who has access to modify the state of the underlying network. To
    achieve this, you MUST reason in depth before choosing to use any of the tools provided to you, as the effect of a miscalculated
    change could severely impact the network. You MUST take as much pre-caution before utilising a tool by reasoning in great depth
    as you would if the underlying network was a critical network which provides constant uptime to thousands of users with NO ROOM 
    FOR DOWNTIME.  A switch can be identified with a datapath id in 16 HEX Format or switch id which is the datapath ID in decimal. 
    Some API calls require the switch ID to be in decimal format (e.g. 0000000000000001 must be passed as 1)
    """

# print(llm)

# p = IntentProcessor(llm, tools, prompt)

# messages = [HumanMessage(content="Host 1 should be able to make SSH connections to Host2. You can assume that Host 1 has an IP of 10.1.1.1 and Host 2 has an IP of 10.1.1.2")]

# result = p.graph.invoke({"messages": messages})

# print(result)
