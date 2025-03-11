import sys

import typer

from otto.api.otto_api import OttoApi
from otto.controller_factory import ControllerFactory
from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import \
    create_tool_list
from otto.shell.otto_shell import OttoShell

"""
def main(model: str = typer.Option(..., prompt=True),
         controller: str = typer.Option(..., prompt=True)
         ):
"""
def main():

    model_fetcher = ModelFactory()
    controller_fetcher = ControllerFactory()
    controller = sys.argv[1]
    model = sys.argv[2]
    api = OttoApi()
    api.run()

    if controller not in ["ryu", "onos"]:
        return

    if model not in ["gpt-4o","gpt-o3-mini", "gpt-4o-mini", "llama", "deepseek", "gemini"]:
        return

    controller = controller_fetcher.get_controller("ryu")

    llm = model_fetcher.get_model(model)

    controller.create_network_state()

    controller.start_state_updater()

    p = IntentProcessor(llm, create_tool_list(), intent_processor_prompt,"User")

    OttoShell("ryu", p, controller).run()


if __name__ == "__main__":
    #typer.run(main)
    main()
