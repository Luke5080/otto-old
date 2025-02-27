import time
from threading import Thread, Event
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
        self._nw_state = NetworkState.get_instance()
        self._nw_db = NetworkDbOperator.get_instance()
        self.stop_event = Event()

    @staticmethod
    def _format_key(key_path: str) -> list:
        """
        Method to format the key of a switch document to be updated when the updater runs.
        e.g. DeepDiff will compare two dictionaries (in our case, the current network state
        -> obtained by querying the APIs available, and the registered network state, held in the MongoDB
        'topology' database). DeepDiff will then return a dictionary of items added/removed and iterable items (elements in
        an array) added/removed. Each of these items are dictionary keys, with the affected elements of the dictionary
        being held in a sub-dictionary in an array. To format the affected key path to be used in a pymongo query,
        some witchcraft needs to be done, and as this is a repetitive task, it is better to follow the DRY principle
        and make a function which does this for us. An example use:
        In: "root['0000000000000001']['connectedHosts']['s1-eth1']['ipv4'][1]"
        Out: ['0000000000000001','connectedHosts','s1-eth1','ipv4',1]

        Appropriate method can now use ".".join(...) to use the returned value in a pymongo query.
        """
        key_path = key_path.replace("root", "").replace("[", "").replace("]", ",").replace("'", "")
        key_path = key_path.split(",")

        del key_path[-1]  # last trailing empty space in list

        return key_path

    def _update_value(self, change: dict) -> list:
        """
        Updates a specific value of a switch document
        """
        updates = []

        for changed_key, new_value in change.items():
            changed_key = self._format_key(changed_key)

            query = {"_id": self._nw_db.object_ids[changed_key.pop(0)]}

            update = {"$set": {".".join(changed_key): new_value['new_value']}}

            updates.append(UpdateOne(query, update))

        return updates

    def _add_value(self, added_value: dict, nw_state: dict) -> list:
        """
        either adding an entire new switch document OR adding a new key to a switch document
        """
        updates = []

        for added_item in added_value:
            added_item = self._format_key(added_item)

            if len(added_item) == 1:
                updates.append(InsertOne(nw_state[added_item[0]]))

            else:
                # weird stuff going on here
                full_update = ".".join(added_item)

                switch_dpid = added_item.pop(0)

                query = {"_id": self._nw_db.object_ids[switch_dpid]}

                update = {"$set": {".".join(added_item): glom(nw_state, full_update)}}

                updates.append(UpdateOne(query, update))

        return updates

    def _remove_value(self, removed_value: dict) -> list:
        """
        either deletes an entire switch document OR deletes a key in a switch document
        """

        updates = []

        for removed_item in removed_value:
            removed_item = self._format_key(removed_item)

            if len(removed_item) == 1:
                query = {"_id": self._nw_db.object_ids[removed_item[0]]}

                updates.append(DeleteOne(query))

            else:
                query = {"_id": self._nw_db.object_ids[removed_item.pop(0)]}

                update = {"$unset": {".".join(removed_item): ""}}

                updates.append(UpdateOne(query, update))

        return updates

    def _remove_ip(self, old_ips: dict) -> list:
        """
        Removes an IP from a switch document's connectHosts.[interface].ipv4 array
        """
        updates = []

        # {"root['0000000000000001']['connectedHosts']['s1-eth1']['ipv4'][1]": '10.1.1.2'}}
        for switch_document, ip in old_ips.items():
            switch_document = self._format_key(switch_document)

            del switch_document[-1]  # removes index of IP to be removed from array - don't need it with $pull

            query = {"_id": self._nw_db.object_ids[switch_document.pop(0)]}

            update = {"$pull": {".".join(switch_document): ip}}

            updates.append(UpdateOne(query, update))

        return updates

    def _add_ip(self, new_ips: dict) -> list:
        """
        Removes an IP from a switch document's connectHosts.[interface].ipv4 array
        """
        updates = []

        # {0000000000000002','connectedHosts','s2-eth1','ipv4',0": '10.1.1.2'},
        for switch_document, ip in new_ips.items():
            switch_document = self._format_key(switch_document)

            query = {"_id": self._nw_db.object_ids[switch_document.pop(0)]}

            update = {"$set": {".".join(switch_document): ip}}

            updates.append(UpdateOne(query, update))

        return updates

    def run(self):
        while not self.stop_event.is_set():
            current_nw_state = {}
            for document in self._nw_state.get_network_state():
                current_nw_state[document["name"]] = document

            diff_found = DeepDiff(self._nw_state.get_registered_state(), current_nw_state)

            if len(diff_found) > 0:
                self._nw_state.construct_network_graph(current_nw_state)

                network_state_db_updates = []

                if "values_changed" in diff_found:
                    network_state_db_updates += self._update_value(diff_found['values_changed'])

                if "dictionary_item_added" in diff_found:
                    network_state_db_updates += self._add_value(diff_found['dictionary_item_added'], current_nw_state)

                if "dictionary_item_removed" in diff_found:
                    network_state_db_updates += self._remove_value(diff_found['dictionary_item_removed'])

                if "iterable_item_added" in diff_found:
                    network_state_db_updates += self._add_ip(diff_found['iterable_item_added'])

                if "iterable_item_removed" in diff_found:
                    network_state_db_updates += self._remove_ip(diff_found['iterable_item_removed'])

                if len(network_state_db_updates) > 0:
                    self._nw_db.bulk_update(network_state_db_updates)

            self.stop_event.wait(60)
