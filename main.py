from otto.ryu.network_state_db.network_state import NetworkState
from otto.ryu.network_state_db.network_state_updater import NetworkStateUpdater
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
import argparse
import toml

def main():

    parser = argparse.ArgumentParser(
        prog="otto - Intent Based Northbound Interface for SDN Controllers",
        description="Declare intents to your Software Defined Network!",
    )

    parser.add_argument("-m", "--model")
    parser.add_argument("-c", "--controller")

    args = parser.parse_args()

    model = args.model

    controller = args.controller

    """
    ns = NetworkState()

    ns.create_network_state_db()

    nsu = NetworkStateUpdater()

    ndo = NetworkDbOperator.get_instance()

    try:
        nsu.start()

    except KeyboardInterrupt:
        ndo.drop_database()
    """
        
if __name__ == "__main__":
    main()
