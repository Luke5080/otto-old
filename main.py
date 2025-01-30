from otto.network_state_db.network_state_creator import NetworkStateCreator

def main():
    db_creator = NetworkStateCreator()
    db_creator.create_network_state_db()

if __name__ == "__main__":
    main()
