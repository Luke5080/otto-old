import argparse
import time
from otto.api.otto_api import OttoApi
from otto.api.otto_gunicorn import GunicornManager
from otto.controller_factory import ControllerFactory
from otto.gui.streamlit_runner import StreamlitRunner
from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.otto_logger.logger_config import logger
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import \
    create_tool_list
from otto.shell.otto_shell import OttoShell
from otto.utils import check_default_credentials, check_api_keys

def main():
    main_arg_parser = argparse.ArgumentParser(prog="Otto",
                                              description="Intent Based Northbound Interface for SDN controllers")

    main_arg_parser.add_argument('--controller', required=True,
                                 help="Controller to be used with Otto - Can either be Ryu or ONOS")

    main_arg_parser.add_argument('--shell-model', required=False, help="Model to be run with OttoShell")

    main_arg_parser.add_argument('--api', action='store_true', help="Turn REST APIs on. Must be enabled to use OttoGui")
    main_arg_parser.add_argument('--gui', action='store_true', help="Turn on OttoGui")

    main_arg_parser.add_argument('--api-pool-size', required=False,
                                 help="IntentProcessor Pool Size to use for Otto REST APIs")
    main_arg_parser.add_argument('--pool-models', required=False,
                                 help="Models to be used in REST API IntentProcessor Pool")

    main_arg_parser.add_argument('--shell', action='store_true', help="Enable shell mode")

    args = main_arg_parser.parse_args()

    if not args.shell and not args.api:
        logger.info("Otto must be started with the --shell or --api flag, or both.")
        return

    if args.controller not in ["ryu", "onos"]:
        logger.info("Controller {args.controller} not available to be used with Otto")
        return

    if args.shell:

        if args.shell_model is None:
            logger.info("Please provide a model to use with OttoShell")
            return

        if args.shell_model not in ["gpt-4o", "gpt-o3-mini", "gpt-4o-mini", "deepseek-chat", "claude-3-5-sonnet"]:
            logger.info(f"Model {args.shell_model} cannot be used with Otto.")
            return

    if args.api:
        otto_flask_api = OttoApi()
        if args.api_pool_size:
            otto_flask_api.intent_processor_pool.pool_size = int(args.api_pool_size)
        if args.pool_models:
            otto_flask_api.intent_processor_pool.models = args.pool_models
        logger.info(
            f"Creating IntentProcessor Pool with a size of {otto_flask_api.intent_processor_pool.pool_size} with models {otto_flask_api.intent_processor_pool.models}")

        otto_flask_api.intent_processor_pool.create_pool()

        gm = GunicornManager(otto_flask_api.app)

    if args.gui:
        if not args.api:
            logger.info("REST APIs must be turned on to run the GUI. Please run with both the --api and --gui flags.")
            return

    controller_fetcher = ControllerFactory()

    controller_env = controller_fetcher.get_controller("ryu")

    controller_env.start_state_broker()
    model_fetcher = ModelFactory()

    llm = model_fetcher.get_model(args.shell_model)

    if args.api:
        gm.start_in_background()
        logger.info("Started REST APIs")

    if args.gui:
        gui_runner = StreamlitRunner()

        gui_runner.start_streamlit()
        logger.info("Started Dashboard: Visit http://localhost:8501")

    if args.shell:
        otto_shell_intent_processor = IntentProcessor(llm, create_tool_list(), intent_processor_prompt, context="User",username="admin")
        time.sleep(0.7) # ultimate groundbreaking fix to prevent logs overlapping shell when running both REST  APIs and GUI at the same time.
        OttoShell("ryu", controller_env, otto_shell_intent_processor, args.api, args.gui).run()


if __name__ == "__main__":
    check_api_keys()
    main()
