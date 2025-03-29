import atexit

from otto.otto_logger.logger_config import logger
from otto.controller_environment import ControllerEnvironment
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
from otto.ryu.network_state_db.network_state_updater import NetworkStateUpdater


class RyuEnvironment(ControllerEnvironment):
    network_state_updater = NetworkStateUpdater()
    network_db_operator = NetworkDbOperator()
    network_db_operator.connect()

    def __init__(self):
        atexit.register(self.drop_database)
        atexit.register(self.stop_state_updater)

    def create_network_state(self):
        self.network_db_operator.create_network_state_db()

    def start_state_updater(self):
        self.network_state_updater.start()

    def stop_state_updater(self):
        logger.debug("Stopping network state updater thread..")
        self.network_state_updater.stop_event.set()
        self.network_state_updater.join()
        logger.debug("Network state updater thread stopped.")

    def drop_database(self):
        logger.debug("Dropping switches collection from otto_network_state_db..")
        self.network_db_operator.drop_database()
        logger.debug("Switches collection dropped.")
