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

    match controller:
        case "ryu":
            controller = controller_fetcher.get_controller("ryu")
        case _:
            return # for now

    match model:
        case "gpt-4o-mini":
            llm = model_fetcher.get_model("gpt-4o-mini")
        case "gpt-4o":
            llm = model_fetcher.get_model("gpt-4o")
        case _:
            raise Exception  # for now

    controller.create_network_state()

    controller.start_state_updater()

    p = IntentProcessor(llm, create_tool_list(), intent_processor_prompt)

    OttoShell("ryu", p).cmdloop()


if __name__ == "__main__":
    typer.run(main)
