from pprint import pprint
import argparse
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from langchain_core.messages import HumanMessage
from otto.intent_utils.agent_prompt import prompt

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
        case "gpt-4o":
            from langchain_openai import ChatOpenAI as llm_lib

    ns = NetworkState()

    ns.create_network_state_db()

    nsu = NetworkStateUpdater()

    ndo = NetworkDbOperator.get_instance()

    llm = llm_lib(model_name=model, temperature=0)

    prompt = ...

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
