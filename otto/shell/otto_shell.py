import argparse
import atexit
import cmd
import sys
from typing import Union

import inquirer
import mysql.connector
from colorama import Fore
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from mysql.connector.abstracts import MySQLConnectionAbstract
from prettytable import PrettyTable
from rich.console import Console
from rich.markdown import Markdown
from yaspin import yaspin

from otto.api.otto_api import OttoApi
from otto.api.otto_gunicorn import GunicornManager
from otto.controller_environment import ControllerEnvironment
from otto.gui.streamlit_runner import StreamlitRunner
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
from otto.utils import check_api_keys
from otto.utils import create_shell_banner


class OttoShell(cmd.Cmd):
    _controller_name: str = None
    _controller_object: ControllerEnvironment
    _agent: IntentProcessor
    _api_endpoints: bool
    _dashboard: bool

    _console: Console
    _model: str = None
    _verbosity_level: str
    _create_app_arg_parser: argparse.ArgumentParser
    _api_endpoint_arg_parser: argparse.ArgumentParser
    _database_connection: MySQLConnectionAbstract
    available_models: dict
    _network_state_db: NetworkDbOperator

    _otto_api: Union[None, OttoApi]
    _gm: Union[None, GunicornManager]
    _gui_runner: Union[None, StreamlitRunner]

    def __init__(self, controller_name: str,
                 controller_object: ControllerEnvironment,
                 agent: IntentProcessor,
                 api_endpoints: bool,
                 dashboard: bool):

        super().__init__()

        self.available_models = {"gpt-4o": "RECOMMENDED", "gpt-4o-mini": "NOT RECOMMENDED", "gpt-o3-mini": "UNSTABLE",
                                 "deepseek-chat": "RECOMMENDED"}

        self._controller_name = controller_name
        self._controller_object = controller_object

        self._agent = agent
        self._model = agent.model_name if not isinstance(agent.model, ChatAnthropic) else agent.model.model

        self._verbosity_level = "VERBOSE"
        self._console = Console()

        self._api_endpoints = api_endpoints
        self._dashboard = dashboard

        self._create_app_arg_parser = argparse.ArgumentParser(prog="Create a network application",
                                                              description="Add app")
        self._create_app_arg_parser.add_argument('--name', required=True, help="app name")
        self._create_app_arg_parser.add_argument('--password', required=True, help="password")

        self._api_endpoint_arg_parser = argparse.ArgumentParser(
            prog="Turn on the REST APIs to be used by network applications and the Otto Dashboard",
            description="Enable REST APIs")
        self._api_endpoint_arg_parser.add_argument('--models', required=False, nargs="+",
                                                   help="Models to be used in IntentProcessorPool. Instances of the IntentProcessor will be configured in an object pool with the desired models.")
        self._api_endpoint_arg_parser.add_argument('--pool-size', required=False,
                                                   help="Size of the IntentProcessorPool to be used to serve API Requests. The pool will be created with the defined size / the amount of models specified")

        self._auth_database_connection = mysql.connector.connect(
            user='root', password='root', host='localhost', port=3306, database='authentication_db'
        )
        self._network_state_db = NetworkDbOperator()

        self._otto_api = None
        self._gm = None
        self._gui_runner = None

        self.prompt = "otto> "

        self.intro = create_shell_banner(model=self._model, controller=self._controller_name,
                                         api_endpoints=self._api_endpoints, dashboard=self._dashboard,
                                         verbosity_level=self._verbosity_level)

        atexit.register(self._close_network_app_db_connection)

    def do_start_api(self, args):
        """ Start the REST API Endpoints """
        if self._api_endpoints:
            print(
                f"{Fore.RED + 'API endpoints are currently on and are running on http://localhost:5000' + Fore.RESET}")

        else:
            args = self._api_endpoint_arg_parser.parse_args(args.split())
            self._otto_api = OttoApi()

            if args.pool_size:
                self._otto_api.intent_processor_pool.pool_size = int(args.pool_size)
            if args.models:
                self._otto_api.intent_processor_pool.models = args.pool_models

            self._gm = GunicornManager(self._otto_api.app)

            self._otto_api.intent_processor_pool.create_pool()
            self._api_endpoints = True

            self._gm.start_in_background()
            print(f"{Fore.GREEN + 'Started REST APIs. Available on http://localhost:5000' + Fore.RESET}")

    def do_start_gui(self, line):
        """ Start the GUI """
        if not self._api_endpoints:
            print(
                f"{Fore.RED + 'Cannot start dashboard as API endpoints are turned off. Please use the command start_api to start the API endpoints' + Fore.RESET}")
            return

        self._gui_runner = StreamlitRunner()

        self._gui_runner.start_streamlit()

        self._dashboard = True
        print(f"{Fore.GREEN + 'Dashboard started and available at http://localhost:8501' + Fore.RESET}")

    def do_get_model(self, line):
        """Print the model which is being used in the IntentProcessor instance"""
        print(self._model)

    def do_get_hosts(self, line):
        """ Get all the current found hosts in the network """
        self._network_state_db.connect()
        network_state = self._network_state_db.dump_network_db()

        host_mappings = {}

        for switch, data in network_state.items():
            for switch_port, remote_host in switch.get('connectedHosts', {}).items():
                host_id = remote_host['id']
                host_mappings[switch] = {}
                host_mappings[switch][switch_port] = host_id

        host_table = PrettyTable()
        host_table_columns = list(host_mappings.keys())
        for switch, port_mapping in host_mappings.items():
            connected_hosts = [f"{port}:{host}" for port, host in port_mapping.items()]

            host_table.add_column(host_table_columns[host_table_columns.index(switch)], connected_hosts)

        print(host_table)

    def do_set_model(self, model):
        """Change the model which is being used in the IntentProcessor agent"""
        if model and model in self.available_models.keys():
            self._agent.change_model(model)
        else:
            print("Model recommendations are based off the evaluation carried out. Results can be found here: ...")
            model_choice = inquirer.list_input("Available Models:",
                                               choices=[f"[{v}]:{k}" for k, v in self.available_models.items()])
            self._agent.change_model(model_choice.split(":")[1])

        self._model = self._agent.model.model_name
        print(f"Changed model to {self._model}")

    def do_set_controller(self, controller):
        """Change the controller being used with Otto. Not implemented yet."""
        if controller and controller in ["ryu", "onos"]:
            self._controller_object = controller
        else:
            self._controller_object = inquirer.list_input("Supported Controllers:", choices=["ryu", "onos"])

    def do_set_verbosity(self, verbosity):
        """ Set the verbosity level of the output of the IntentProcessor agent"""
        if verbosity and verbosity in ["LOW", "VERBOSE"]:
            self._verbosity_level = verbosity
        else:
            self._verbosity_level = inquirer.list_input("Verbosity Levels:", choices=["LOW", "VERBOSE"])
        print(f"Agent verbosity set to {self._verbosity_level}")

    def verbose_output(self, intent):
        for output in self._agent.graph.stream({"messages": intent}):
            if 'save_intent' in output:
                continue
            for key, value in output.items():
                if 'messages' in value:
                    self._console.print(Markdown(f"**STEP: {key.replace('_', ' ').upper()}**"))
                    if isinstance(value['messages'][-1].content, str):
                        self._console.print(Markdown(value['messages'][-1].content))
                    elif isinstance(value['messages'][-1].content, list):
                        self._console.print(Markdown(value['messages'][-1].content[0].get('text', '')))

    def non_verbose_output(self, intent):
        with yaspin(text="Attempting to fulfill intent..", color="cyan") as sp:
            result = self._agent.graph.invoke({"messages": intent})
            sp.ok()
        self._console.print(Markdown(f"**Operations completed:**\n{result['operations']}"))

    def do_intent(self, intent):
        messages = [HumanMessage(content=intent)]

        if self._verbosity_level == "VERBOSE":
            self.verbose_output(messages)
        else:
            self.non_verbose_output(messages)

    def do_create_app(self, args):
        try:
            args = self._create_app_arg_parser.parse_args(args.split())

            cursor = self._auth_database_connection.cursor()

            cursor.execute(
                f"INSERT INTO network_applications(username, password) VALUES(%s, %s)", (args.name, args.password)
            )

            cursor.fetchall()

        except SystemExit:
            pass

    def do_exit(self, arg):
        self._controller_object.stop_state_updater()
        sys.exit(0)

    def run(self):
        check_api_keys()
        shell_exit = False
        while not shell_exit:
            try:
                self.cmdloop()
            except KeyboardInterrupt:
                print("Interrupt caught: please use the 'exit' command to exit gracefully.")

    def do_EOF(self, line):
        return True

    def postloop(self):
        return True

    def emptyline(self):
        pass

    def _close_network_app_db_connection(self) -> None:
        self._database_connection.close()
