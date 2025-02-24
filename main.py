import typer
from otto.ryu.intent_engine.intent_processor_agent_tools import create_tool_list
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.shell.otto_shell import OttoShell
from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.controller_factory import ControllerFactory


def main(model: str = typer.Option(..., prompt=True),
         controller: str = typer.Option(..., prompt=True)
         ):

    model_fetcher = ModelFactory()
    controller_fetcher = ControllerFactory()

    if controller not in ["ryu", "onos"]:
        return

    if model not in ["gpt-4o", "gpt-4o-mini"]:
        return

    controller = controller_fetcher.get_controller("ryu")

    llm = model_fetcher.get_model(model)

    controller.create_network_state()

    controller.start_state_updater()

    p = IntentProcessor(llm, create_tool_list(), intent_processor_prompt,"User")

    OttoShell("ryu", p, controller).run()


if __name__ == "__main__":
    typer.run(main)
