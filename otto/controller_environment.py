from abc import ABC, abstractmethod


class ControllerEnvironment(ABC):
    @property
    @abstractmethod
    def network_state_broker(self):
        pass

    @abstractmethod
    def start_state_broker(self):
        pass

    @abstractmethod
    def stop_state_broker(self):
        pass
