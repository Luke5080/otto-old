import requests
import streamlit as st
from requests import HTTPError

from exceptions import AuthenticationError, ApiRequestError


class ApiHandler:
    def __init__(self):
        self._authentication_token = None
        self._login_headers = {'Content-Type': 'application/json'}
        self._request_headers = {'Authorization': f'Bearer {self._authentication_token}'}
        self._api_url = "http://127.0.0.1:5000"

    @st.cache_resource(ttl=None)
    @staticmethod
    def get_api_handler():
        return ApiHandler()

    def login(self, username: str, password: str) -> requests.Response:
        """
        Args:
            username: str
            password: str

        Method to authenticate user against authentication_db:users.
        Returns Response Object to be handled appropriately in streamlit app
        """

        login_data = {'method': 'user', 'username': username, 'password': password}

        try:
            authentication_response = requests.post(f"{self._api_url}/login", headers=self._login_headers,
                                                    json=login_data)
        except HTTPError as e:
            raise AuthenticationError(
                f"Error while authenticating user. Please ensure Otto is running with API endpoints enabled. Error: {e}")

        return authentication_response

    def set_token(self, token: str) -> None:
        """
        Args:
             token: str - JWT token for user authentication

        Method to set token attribute to the authentication token obtained through login
        """

        self._authentication_token = token
        self._request_headers['Authorization'] = f"Bearer {self._authentication_token}"

    def get_latest_activity(self) -> dict:
        """
        Method to retrieve the latest activity data from the /latest-activity API. Returns the last 5 documents
        found in the intent_history collection in the processed_intents_db database.
        """

        try:
            latest_activity_response = requests.get(f"{self._api_url}/latest-activity", headers=self._request_headers)
            latest_activity_response.raise_for_status()

        except HTTPError as e:
            raise ApiRequestError(f"""
            Error while retrieving data from {self._api_url}/latest-activity
            Ensure that otto is running with the Gunicorn server running\nError: {e}
            """)

        except Exception as e:
            raise ApiRequestError(f"Error while retrieving data from {self._api_url}/latest-activity: {e}")

        return latest_activity_response.json().get('message', "")

    def get_weekly_activity(self) -> dict:
        """
        Method to retrieve the weekly activity data from the /weekly-activity API. Returns a dictionary, where each
        dictionary key is a timestamp, and each value is a count of intents declared.
        """
        try:
            weekly_activity_response = requests.get(f"{self._api_url}/weekly-activity", headers=self._request_headers)

        except HTTPError as e:
            raise ApiRequestError(f"""
            Error while retrieving data from {self._api_url}/latest-activity
            Ensure that otto is running with the Gunicorn server running\nError: {e}
            """)

        except Exception as e:
            raise ApiRequestError(f"Error while retrieving data from {self._api_url}/latest-activity: {e}")

        return weekly_activity_response.json().get('message', "")

    def get_top_activity(self) -> dict:
        """
        Method to retrieve usage per user/application. Returns a dictionary where each key is the name of a user/application,
        and each value is the number of intents declared
        """
        try:
            top_activity_response = requests.get(f"{self._api_url}/top-activity", headers=self._request_headers)

        except HTTPError as e:
            raise ApiRequestError(f"""
                                  Error while retrieving data from {self._api_url}/latest-activity
                                  Ensure that otto is running with the Gunicorn server running\nError: {e}
                                  """)
        except Exception as e:
            raise ApiRequestError(f"Error while retrieving data from {self._api_url}/latest-activity: {e}")

        return top_activity_response.json().get('message', "")

    def get_model_usage(self) -> dict:
        """
        Method to retrieve usage per user/application. Returns a dictionary where each key is the name of a user/application,
        and each value is the number of intents declared
        """
        try:
            model_usage_response = requests.get(f"{self._api_url}/model-usage", headers=self._request_headers)

        except HTTPError as e:
            raise ApiRequestError(f"""
                Error while retrieving data from {self._api_url}/model-usage. 
                Ensure that otto is running with the Gunicorn server running\nError: {e}
                """)
        except Exception as e:
            raise ApiRequestError(f"Error while retrieving data from {self._api_url}/model-usage: {e}")

        return model_usage_response.json().get('message', "")

    def declare_intent(self, intent: str, model: str) -> dict:
        """
        Method to send intent to be processed and fulfilled by sending a POST request
        to /declare-intent endpoint. Returns response in JSON format

        Args:
            intent: str - Intent in string format to be sent to /declare-intent API.
        """
        data = {'method': 'admin', 'token': self._authentication_token, 'intent': intent,
                'stream_type': 'AgentMessages', 'model': model}

        try:
            response = requests.post(f"{self._api_url}/declare-intent", headers=self._request_headers, json=data)

        except HTTPError as e:
            raise ApiRequestError(f"""
                Error while declaring intent to {self._api_url}/declare-intent.
                Ensure that otto is running with the Gunicorn server running\nError: {e}
                """)
        except Exception as e:
            raise ApiRequestError(f"Error while declaring intent to {self._api_url}/declare-intent: {e}")

        return response.json()
