from threading import Thread, Event

from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder


class NetworkStateBroker(Thread):
    _nw_state_finder: NetworkStateFinder

    def __init__(self):
        self._nw_state_finder = NetworkStateFinder()
        self.agent_run_network_state_given = {}
        self.stop_event = Event()

        super().__init__()

    def provide_network_state(self, agent_run_id: str) -> dict:
        """
        Method to provide the current network state to an agent. An agent will call
        this method with the ID of the current agent run, and the method will provide
        the current network state found through the get_network_state method in the
        NetworkStateFinder class. A dictionary containing agent run IDs mapped with the
        network state ID is created, to be checked in the run method of the thread.

        Returns:
            Dictionary containing the current network state.
        """
        found_network_state = self._nw_state_finder.get_network_state()
        state_id = next(iter(found_network_state), None)

        if state_id is None:
            raise Exception("State ID is None.")

        self.agent_run_network_state_given[agent_run_id] = state_id

        return found_network_state

    def terminate_agent_run(self, agent_run_id: str) -> None:
        """
        Removes the agent run ID from the agent_run_network_state_given dictionary once
        an agent has finished executing.
        """

        try:
            print("Deleting...")
            del self.agent_run_network_state_given[agent_run_id]

        except KeyError as e:
            raise Exception(f"Could not find ID for the provided agent run: {e}")

        except Exception as e:
            raise Exception(f"An error occurred whilst attempting to unregister the agent run: {e}")

    def run(self):
        """
        Overwritten run method of the parent Thread class. While the event is not set,
        go through each
        """

        while not self.stop_event.is_set():
            for agent_run, given_network_state in self.agent_run_network_state_given.items():
                print(f"Checking {agent_run} with state {given_network_state}")
                current_network_state = self._nw_state_finder.get_network_state()

                if current_network_state != given_network_state:
                    print("Changes Found in Network State. Need to interrupt agent..")

            self.stop_event.wait(10)
