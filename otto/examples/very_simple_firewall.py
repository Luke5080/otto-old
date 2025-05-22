import sys
from pathlib import Path

import pyfiglet
import requests
import toml
from prettytable import PrettyTable
from requests import HTTPError
from yaspin import yaspin


class SimpleFirewall:
    def __init__(self):
        self._authentication_token = None
        self._username = "firewall101"
        self._password = "firewall.123"
        self._login_body = {"method": "application", "username": self._username, "password": self._password}

        self._login_headers = {'Content-Type': 'application/json'}
        self._request_headers = {'Authorization': f'Bearer {self._authentication_token}'}
        self._api_url = "http://127.0.0.1:5000"

        self.firewall_rules = PrettyTable()
        self.firewall_rules.field_names = ["ID", "Source", "Destination", "Protocol", "Action"]

        self._rules_file = Path("/tmp/firewall_rules.toml")

    def _authenticate(self) -> None:
        try:
            authentication_response = requests.post(f"{self._api_url}/login", headers=self._login_headers,
                                                    json=self._login_body)
        except HTTPError as e:
            raise Exception(
                f"Error while authenticating application. Please ensure Otto is running with API endpoints enabled. Error: {e}")

        if authentication_response.json().get('token', ''):
            self._authentication_token = authentication_response.json()['token']
            self._request_headers['Authorization'] = f"Bearer {self._authentication_token}"

        else:
            raise Exception(
                f"Could not retrieve Authentication Token from response: {authentication_response.json()}")

    def _add_rule(self):

        allowed_actions = ["ALLOW", "BLOCK"]
        source = str(input("Source: "))

        destination = str(input("Destination: "))

        protocol = str(input("Protocol: "))

        while True:
            action = str(input("Action: "))

            if action in allowed_actions:
                break
            else:
                print("Action can only be: ALLOW or BLOCK")

        if self._declare_intent(source, destination, protocol, action):
            print("Rule Added")

        else:
            print("Could not add rule")

    @yaspin(text="Adding Firewall Rule..")
    def _declare_intent(self, src: str, dst: str, protocol: str, action: str) -> bool:
        self._authenticate()

        if action == "ALLOW":
            intent = {"intent": f"{src} should be able to connect to {dst} via {protocol}"}
        else:
            intent = {"intent": f"{src} should not be able to connect to {dst} via {protocol}", "model": "gpt-4o"}

        try:
            response = requests.post(f"{self._api_url}/declare-intent", headers=self._request_headers, json=intent)
            response.raise_for_status()

        except HTTPError as e:
            raise Exception(f"""
                Error declaring into to {self._api_url}/declare-intent
                Ensure that otto is running with the Gunicorn server running\nError: {e}
                """)

        except Exception as e:
            raise Exception(f"""
                            Error declaring into to {self._api_url}/declare-intent
                            Ensure that otto is running with the Gunicorn server running\nError: {e}
                            """)

        if response.status_code == 200:
            with open("/tmp/firewall_rules.toml", "r") as f:
                rules = toml.load(f)

            rule_id = len(rules) + 1

            new_rule = {
                "source": src,
                "destination": dst,
                "protocol": protocol,
                "action": action
            }
            rules[str(rule_id)] = new_rule

            with open("/tmp/firewall_rules.toml", "w") as f:
                toml.dump(rules, f)

            self.firewall_rules.add_row([rule_id, src, dst, protocol, action])
            return True

        return False

    def load_rules(self):
        rules = {}

        if self._rules_file.exists():
            with open("/tmp/firewall_rules.toml", "r") as f:
                rules = toml.load(f)
        else:
            self._rules_file.touch()

        for rule_id, rule in rules.items():
            self.firewall_rules.add_row(
                [rule_id, rule['source'], rule['destination'], rule['protocol'], rule['action']])

    def menu(self):

        self.load_rules()

        print(pyfiglet.figlet_format('VSFirewall', font='dos_rebel'))
        print("""
        Welcome to Very Simple Firewall!
        
        Simple Firewall Application To Demonstrate Otto's Capabilities
        """)

        choices = ["Add Rule", "Close"]

        while True:
            print(self.firewall_rules)

            print("Please Choose an Option")
            for index, choice in enumerate(choices):
                print(f"[{index + 1}]: {choice}")
            try:
                user_choice = int(input(">>> "))

            except ValueError:
                print("Invalid Option")

            if user_choice > 2 or user_choice < 1:
                print("Invalid Option")

            if user_choice == 1:
                self._add_rule()

            else:
                print("Bye!")
                sys.exit(0)


if __name__ == "__main__":
    firewall = SimpleFirewall()
    firewall.menu()
