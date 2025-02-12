from langchain_community.chat_models import ChatOpenAI
from langchain_core.tools import tool, render_text_description
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from otto.ryu.intent_engine.agent_base import AgentBase
from otto.ryu.intent_engine.agent_prompts import AgentPrompts
import requests
from otto.ryu.network_state_db.network_state import NetworkState

class ModifyNetworkAgent(AgentBase):
    _prompt_holder = AgentPrompts()

    agent_prompt: str = _prompt_holder.modify_network_agent_prompt

    @staticmethod
    def network_state():
        ns = NetworkState()

        return ns.get_registered_state()

    @staticmethod
    def add_rule(config) -> int:
        config = eval(config)
        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            "dpid": config["id"],
            "cookie": 0,
            "table_id": config["t_id"],
            "priority": 100,
            "match": config["match"],
            "actions": config["actions"]
        }
        print(data)
        resp = requests.post('http://localhost:8080/stats/flowentry/add', headers=headers, json=data)

        return resp.status_code

    @staticmethod
    def delete_rule(config) -> int:
        config = eval(config)

        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            "dpid": config["id"],
            "cookie": 0,
            "table_id": config["t_id"],
            "priority": 100,
            "match": config["match"],
            "actions": config["actions"]
        }

        resp = requests.post('http://localhost:8080/stats/flowentry/delete_strict', headers=headers, json=data)

        return resp.status_code

    @tool
    def get_network_state(self):
        """
        Get the current entire state of the network
        """
        return self.network_state()

    @tool
    def add_rule_to_switch(self, config) -> int:
        """
        Function to add an OpenFlow rule to a switch. Function
        takes the switch id as a paramtre, as well as dictionary holding flow parametres named config.
        config must include the switch id, passed as id, which is an integer referring to the switch id
        config  must include the table id, passed as t_id,
        which is an integer refering to the table id where the flow should
        be installed. config must include 'match',
        which will hold a dicitonary of match criteria for the rule. Inside the
        dictionary, include the dl_type, the nw_src, the nw_dst, the nw_proto and
        the tp_dst. config must include "actions" and is a list of actions to be
        done if the flow criteria is matched. for the action to drop packets, this
        should be an empty list, but if it is to output on a port, use the format:
        "actions":[{"type":"OUTPUT", "port": 2}]
        """

        return self.add_rule(config)

    @tool
    def delete_rule_on_switch(self, config) -> int:
        """
        Function to remove an OpenFlow rule to a switch. Function
        takes the switch id as a paramtre, as well as dictionary holding flow parametres named config.
        This function removes a rule which meets the exact criteria outlined in
        config must include the switch id, passed as id, which is an integer referring to the switch id
        config  must include the table id, passed as t_id,
        which is an integer refering to the table id where the flow should
        be installed. config must include 'match',
        which will hold a dicitonary of match criteria for the rule. Inside the
        dictionary, include the dl_type, the nw_src, the nw_dst, the nw_proto and
        the tp_dst. config must include "actions" and is a list of actions to be
        done if the flow criteria is matched.

        """

        return self.delete_rule(config)

    agent_tools: list = [add_rule_to_switch, delete_rule_on_switch, get_network_state]

    agent_tool_descriptions: str = render_text_description(agent_tools)

    input_variables = ["input", "agent_scratchpad"]

    agent_prompt_template: PromptTemplate = PromptTemplate(
        template=agent_prompt,
        input_variables=input_variables,
        partial_variables={
            "tools": agent_tool_descriptions,
            "tool_names": ", ".join([t.name for t in agent_tools])
        }
    )

    def create_agent(self):
        llm = ChatOpenAI(model_name="gpt-4o-mini")

        agent = create_react_agent(
            llm=llm,
            tools=self.agent_tools,
            prompt=self.agent_prompt_template
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.agent_tools,
            handle_parsing_errors=True,
            verbose=True,
            max_iterations=10
        )

        return agent_executor


