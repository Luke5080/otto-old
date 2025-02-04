from otto.network_state_db.network_state import NetworkState
from otto.network_state_db.network_state_updater import NetworkStateUpdater

def main():
    ns = NetworkState()

    ns.create_network_state_db()

    nsu = NetworkStateUpdater()

    nsu.start()

if __name__ == "__main__":
    main()
