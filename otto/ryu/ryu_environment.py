import atexit

from otto.controller_environment import ControllerEnvironment
from otto.otto_logger.logger_config import logger
from otto.ryu.network_state_db.network_state_broker import NetworkStateBroker


class RyuEnvironment(ControllerEnvironment):
    network_state_broker = NetworkStateBroker()

    def __init__(self):
        atexit.register(self.stop_state_broker)

    def start_state_broker(self):
        self.network_state_broker.start()

    def stop_state_broker(self):
        logger.debug("Stopping network state broker thread..")
        self.network_state_broker.stop_event.set()
        self.network_state_broker.join()
        logger.debug("Network state broker thread stopped.")
