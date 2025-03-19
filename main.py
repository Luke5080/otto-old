import multiprocessing

import typer

from otto.api.otto_api import OttoApi
from otto.api.otto_gunicorn import GunicornManager
from otto.controller_factory import ControllerFactory
from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import \
    create_tool_list
from otto.shell.otto_shell import OttoShell


def main(model: str = typer.Option(..., prompt=True),
         controller: str = typer.Option(..., prompt=True),
         shell: bool = typer.Option(False, "--shell", is_flag=True)
         ):

    # create controller factory to return our controller object
    controller_fetcher = ControllerFactory()

    # get our controller object
    controller = controller_fetcher.get_controller("ryu")

    # create our associated network state for our controller and start its updates.
    controller.create_network_state()
    controller.start_state_updater()

    otto_flask_api = OttoApi.get_instance()

    model_fetcher = ModelFactory()

    if controller not in ["ryu", "onos"]:
        return

    if model not in ["gpt-4o", "gpt-o3-mini", "gpt-4o-mini", "llama", "deepseek", "gemini"]:
        return

    llm = model_fetcher.get_model(model)

    p = IntentProcessor(llm, create_tool_list(), intent_processor_prompt, "User")

    if not shell:
       gm = GunicornManager.get_instance(otto_flask_api.app)

       gm.run()

    if shell:
        OttoShell("ryu", p, controller).run()


if __name__ == "__main__":
    typer.run(main)
