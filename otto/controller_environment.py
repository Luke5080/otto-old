from abc import ABC, abstractmethod


class ControllerEnvironment(ABC):
    @property
    @abstractmethod
    def network_db_operator(self):
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

    @abstractmethod
    def stop_state_updater(self):
        pass

    @abstractmethod
    def drop_database(self):
        pass


