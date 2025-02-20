from abc import ABC, abstractmethod


class ControllerEnvironment(ABC):
    @property
    @abstractmethod
    def network_db_operator(self):
        pass

    @property
    @abstractmethod
    def network_state(self):
        pass

    @property
    @abstractmethod
    def network_state_finder(self):
        pass

    @property
    @abstractmethod
    def network_state_updater(self):
        pass

    @abstractmethod
    def create_network_state(self):
        pass

    @abstractmethod
    def start_state_updater(self):
        pass
