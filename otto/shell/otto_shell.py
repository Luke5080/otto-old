import argparse
import atexit
import cmd
import sys

import inquirer
import mysql.connector
from langchain_core.messages import HumanMessage
from prettytable import PrettyTable
from rich.console import Console
from rich.markdown import Markdown
from yaspin import yaspin

from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.ryu_environment import RyuEnvironment


class OttoShell(cmd.Cmd):
    _console: Console
    _model: str = None
    _controller_object: RyuEnvironment  # FIXME
    _controller: str = None
    _agent: IntentProcessor
    _verbosity_level: str
    _create_app_arg_parser: argparse.ArgumentParser

    def __init__(self, controller, agent, controller_object):
        super().__init__()
        self.available_models = ["gpt-4o", "gpt-4o-mini", "llama", "deepseek", "gemini", "gpt-o3-mini"]
        self._controller = controller
        self._agent = agent
        self._model = agent.model.model_name
        self._verbosity_level = "VERBOSE"
        self._controller_object = controller_object
        self._console = Console()

        atexit.register(self._close_network_app_db_connection)
        self._create_app_arg_parser = argparse.ArgumentParser(prog="Create a network application",
                                                              description="Add app")
        self._create_app_arg_parser.add_argument('--name', required=True, help="app name")
        self._create_app_arg_parser.add_argument('--password', required=True, help="password")
        self._database_connection = mysql.connector.connect(
            user='root', password='root', host='localhost', port=3306, database='authentication_db'
        ) # change this

        self.prompt = "otto> "

        self.intro = f"""
        Otto - Intent Based Northbound Interface for SDN Controllers
        Author: Luke Marshall

        Configured model: {self._model}
        Configured Controller: {self._controller}

        Agent Output Verbosity Level: {self._verbosity_level}
        """

    def do_get_model(self, line):
        print(self._model)

    def do_get_hosts(self, line):
        host_table = PrettyTable()
        host_table_columns = list(self._controller_object.network_state.host_mappings)
        for switch, port_mapping in self._controller_object.network_state.host_mappings.items():
            connected_hosts = [f"{port}:{host}" for port, host in port_mapping.items()]

            host_table.add_column(host_table_columns[host_table_columns.index(switch)], connected_hosts)

        print(host_table)

    def do_set_model(self, model):
        if model and model in self.available_models:
            self._agent.change_model(model)
        else:
            model_choice = inquirer.list_input("Available Models:", choices=self.available_models)
            self._agent.change_model(model_choice)

        self._model = self._agent.model.model_name
        print(f"Changed model to {self._model}")

    def do_set_controller(self, controller):
        if controller and controller in ["ryu", "onos"]:
            self._controller = controller
        else:
            self._controller = inquirer.list_input("Supported Controllers:", choices=["ryu", "onos"])

    def do_set_verbosity(self, verbosity):
        if verbosity and verbosity in ["LOW", "VERBOSE"]:
            self._verbosity_level = verbosity
        else:
            self._verbosity_level = inquirer.list_input("Verbosity Levels:", choices=["LOW", "VERBOSE"])
        print(self._verbosity_level)

    def verbose_output(self, intent):
        for output in self._agent.graph.stream({"messages": intent}):
            if 'save_intent' in output:
                continue
            for key, value in output.items():
                if 'messages' in value:
                    self._console.print(Markdown(f"**STEP: {key.replace('_', ' ').upper()}**"))
                    self._console.print(Markdown(value['messages'][-1].content))
                if 'intent_understanding' in value:
                    self._console.print(Markdown(value['intent_understanding'].content))

                if 'operations' in value:
                    self._console.print(Markdown(f"**Operations completed**:\n{value['operations']}"))

    @yaspin(text="Attempting to fulfill intent..")
    def non_verbose_output(self, intent):
        result = self._agent.graph.invoke({"messages": intent})

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

            cursor = self._database_connection.cursor()

            cursor.execute(
                f"INSERT INTO network_applications(app_name, password) VALUES(%s, %s)", (args.name, args.password)
            )

            self._database_connection.commit()

            cursor.fetchall()

        except SystemExit:
            pass

    def do_exit(self, arg):
        self._controller_object.stop_state_updater()
        sys.exit(0)

    def run(self):
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

    def _close_network_app_db_connection(self) -> None:
        self._database_connection.close()
