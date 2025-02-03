from otto.network_state_db.network_state import NetworkState

def main():
    ns = NetworkState()

    ns.create_network_state()

    print(ns.current_network_state)

if __name__ == "__main__":
    main()
