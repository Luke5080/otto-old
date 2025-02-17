from pprint import pprint
import argparse
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from langchain_core.messages import HumanMessage

def main():
    parser = argparse.ArgumentParser(
        prog="otto - Intent Based Northbound Interface for SDN Controllers",
        description="Declare intents to your Software Defined Network!",
    )

    parser.add_argument("-m", "--model")
    parser.add_argument("-c", "--controller")

    args = parser.parse_args()

    model = args.model

    controller = args.controller

    match controller:
        case "ryu":
            from otto.ryu.network_state_db.network_state import NetworkState
            from otto.ryu.network_state_db.network_state_updater import NetworkStateUpdater
            from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
        case _:
            return  # for now

    match model:
        case "gpt-4o-mini":
            from langchain_openai import ChatOpenAI as llm_lib

    ns = NetworkState()

    ns.create_network_state_db()

    nsu = NetworkStateUpdater()

    ndo = NetworkDbOperator.get_instance()

    llm = llm_lib(model_name=model, temperature=0)

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
    Some API calls require the switch ID to be in decimal format (e.g. 0000000000000001 must be passed as 1). After each successful tool execution, you MUST call the "check_element" tool to verify the state of the switch affected by the previous operation. Ensure that you pass the correct switch ID (in decimal format) when invoking "check_element".
    Switch ports for a switch are described with a port number, hardware address and name. When setting up flow rules, be sure to use the decimal version of the port number (e.g. 00000002 is 2) in the actions field of the tool calls.
    """

    toolkit = create_tool_list()

    p = IntentProcessor(llm, toolkit, prompt)

    nsu.start()


    while True:
        user_intent = str(input(">>> "))
        messages = [HumanMessage(content=user_intent)]

        result = p.graph.invoke({"messages": messages})

        pprint(result)


if __name__ == "__main__":
    main()
