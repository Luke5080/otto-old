import time
from threading import Thread
from otto.network_state_db.network_state import NetworkState
from otto.network_state_db.network_db_operator import NetworkDbOperator
from deepdiff import DeepDiff
from pymongo import UpdateOne
import sys

class NetworkStateUpdater(Thread):
    _nw_state : NetworkState
    _nw_db : NetworkDbOperator

    def __init__(self):
        super().__init__()
        self._nw_state = NetworkState()
        self._nw_db = NetworkDbOperator()

    def update_value(self, change: dict) -> None:

        updates = []

        # really weird string manipulation to make this work
        for changed_key, new_value in change.items():
            changed_key = changed_key.replace("root", "").replace("[", "").replace("]", ",").replace("'", "")
            changed_key = changed_key.split(",")

            del changed_key[-1] # last trailing empty space in list

            q_id = changed_key.pop(0)

            update = {"$set": {".".join(changed_key) : new_value['new_value']}}

            query = {"name" : q_id}

            updates.append(UpdateOne(query, update))

        self._nw_db.bulk_update(updates)

    def run(self):
        while True:
            print("Starting..")
            current_nw_state = {}
            for document in self._nw_state.get_network_state():
                current_nw_state[document["name"]] = document

            diff_found = DeepDiff(self._nw_state.get_registered_state(),current_nw_state)

            if len(diff_found) > 0:
                print(diff_found)
                self.update_value(diff_found['values_changed'])
                print("done")

            time.sleep(60)
