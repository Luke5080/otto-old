import time
from threading import Thread
from otto.ryu.network_state_db.network_state import NetworkState
from otto.ryu.network_state_db.network_db_operator import NetworkDbOperator
from deepdiff import DeepDiff
from pymongo import UpdateOne, DeleteOne, InsertOne
from glom import glom


class NetworkStateUpdater(Thread):
    _nw_state: NetworkState
    _nw_db: NetworkDbOperator

    def __init__(self):
        super().__init__()
        self._nw_state = NetworkState()
        self._nw_db = NetworkDbOperator.get_instance()

    def _update_value(self, change: dict) -> None:
        updates = []

        # really weird string manipulation to make this work
        for changed_key, new_value in change.items():
            changed_key = changed_key.replace("root", "").replace("[", "").replace("]", ",").replace("'", "")
            changed_key = changed_key.split(",")

            del changed_key[-1]  # last trailing empty space in list

            query = {"_id": self._nw_db.object_ids[changed_key.pop(0)]}

            update = {"$set": {".".join(changed_key): new_value['new_value']}}

            updates.append(UpdateOne(query, update))

        self._nw_db.bulk_update(updates)

    def _add_value(self, added_value: dict, nw_state: dict) -> None:
        """
        either adding an entire new switch document OR adding a new key to a switch document
        """
        updates = []

        for added_item in added_value:
            added_item = added_item.replace("root", "").replace("[", "").replace("]", ",").replace("'", "")
            added_item = added_item.split(",")

            del added_item[-1]

            if len(added_item) == 1:
                updates.append(InsertOne(nw_state[added_item[0]]))

            else:
                # weird stuff going on here
                full_update = ".".join(added_item)

                switch_dpid = added_item.pop(0)

                query = {"_id": self._nw_db.object_ids[switch_dpid]}

                update = {"$set": {".".join(added_item): glom(nw_state, full_update)}}

                updates.append(UpdateOne(query, update))

        self._nw_db.bulk_update(updates)

    def _remove_value(self, added_value: dict, nw_state: dict) -> None:
        """
        either deletes an entire switch document OR deletes a key in a switch document
        """

        updates = []

        for added_item in added_value:
            added_item = added_item.replace("root", "").replace("[", "").replace("]", ",").replace("'", "")
            added_item = added_item.split(",")

            del added_item[-1]

            if len(added_item) == 1:
                query = {"_id": self._nw_db.object_ids[added_item[0]]}

                updates.append(DeleteOne(query))

            else:
                query = {"_id": self._nw_db.object_ids[added_item.pop(0)]}

                update = {"$unset": {".".join(added_item): ""}}

                updates.append(UpdateOne(query, update))

        self._nw_db.bulk_update(updates)

    def run(self):
        while True:
            print("Starting..")
            current_nw_state = {}
            for document in self._nw_state.get_network_state():
                current_nw_state[document["name"]] = document

            diff_found = DeepDiff(self._nw_state.get_registered_state(), current_nw_state)

            if len(diff_found) > 0:
                print(diff_found)
                if "values_changed" in diff_found:
                    self._update_value(diff_found['values_changed'])

                if "dictionary_item_added" in diff_found:
                    self._add_value(diff_found['dictionary_item_added'], current_nw_state)

                if "dictionary_item_removed" in diff_found:
                    self._remove_value(diff_found['dictionary_item_removed'], current_nw_state)

                print("done")

            time.sleep(60)
