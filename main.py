from otto.ryu.network_state_db.network_state import NetworkState
from otto.ryu.network_state_db.network_state_updater import NetworkStateUpdater
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator

def main():
    ns = NetworkState()

    ns.create_network_state_db()

    nsu = NetworkStateUpdater()

    ndo = NetworkDbOperator.get_instance()

    try:
        nsu.start()

    except KeyboardInterrupt:
        ndo.drop_database()
        
if __name__ == "__main__":
    main()
