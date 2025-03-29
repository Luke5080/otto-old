from typing import Union
from bson import ObjectId
from pymongo import MongoClient, InsertOne
from pymongo.errors import PyMongoError

from exceptions import (NetworkDatabaseException,
                        SwitchDocumentNotFound)
from otto.ryu.network_state_db.network_state_finder import NetworkStateFinder


class NetworkDbOperator:
    _MongoConnector: Union[None, MongoClient]
    _network_state_finder: NetworkStateFinder

    def __init__(self):
        self._MongoConnector = None
        self._network_state_db = None
        self._switch_collection = None
        self._network_state_finder = NetworkStateFinder()

    def connect(self):
        """
        Connect method to be used when wishing to connect to the network_state_db.
        This is run after the object has been created, and created within the process which will
        connect to the database to prevent any forking issues.
        """
        if self._MongoConnector is None:
            self._MongoConnector = MongoClient('localhost', 27017)

            self._network_state_db = self._MongoConnector["topology"]
            self._switch_collection = self._network_state_db["switches"]

    def get_network_state(self) -> dict:
        """
        Method to find the current network state. Uses NetworkStateFinder to get a list of current
        switches found in the network. Once the switches have been found, use the get_switch_details method
        to create a document to be inputted into the topology.switches collection.

        Yields:
            dict: document for a switch to be inputted into topology.switches
        """
        found_switches = self._network_state_finder.get_switches()

        for switch in found_switches:
            switch_info = self._network_state_finder.get_switch_details(str(switch))
            yield switch_info

    def create_network_state_db(self):
        """
        Method to create the switches collection in otto_network_state_db.topology. This method should be called
        by any child class of ControllerEnvironment when creating the initial network_state_db to be used for the remainder
        of the program lifetime. The topology.switches collection will be updated periodically by the NetworkStateUpdater
        """
        self.drop_database()  # delete topology collection if it already exists

        switches  = []

        for found_switch in self.get_network_state():
            found_switch['_id'] = ObjectId()
            switches.append(InsertOne(found_switch))

        self._switch_collection.bulk_write(switches)
    def put_switch_to_db(self, switch_struct: dict) -> None:
        try:
            inserted_doc = self._switch_collection.insert_one(switch_struct)

            return inserted_doc.inserted_id

        except PyMongoError as e:
            raise NetworkDatabaseException(
                f"""
                Exception occurred while attempting to put a document into MongoDB.
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise NetworkDatabaseException(e)

    def modify_switch_document(self, switch_dpid: str, change: dict) -> None:

        match_exp = {'_id': self.object_ids[switch_dpid]}

        try:
            self._switch_collection.update_one(match_exp, change)
        except PyMongoError as e:
            raise NetworkDatabaseException(
                f"""
                    Exception occurred while attempting to modify a document for {switch_dpid}.
                    Exception raised: {e}
                    """
            )

    def remove_switch_document(self, switch_dpid: str) -> None:

        try:
            self._switch_collection.delete_one({"_id": self.object_ids[switch_dpid]})
            del self.object_ids[switch_dpid]

        except PyMongoError as e:
            raise NetworkDatabaseException(
                f"""
                Exception occurred while attempting to remove a document in MongoDB.
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise NetworkDatabaseException(e)

    def get_switch_document(self, switch_dpid: str, **kwargs):
        try:
            match = {"_id": self.object_ids[switch_dpid]}

            if len(kwargs) > 0:
                match = {**match, **kwargs}

            switch_entry = self._switch_collection.find_one(match)

        except PyMongoError as e:
            raise NetworkDatabaseException(
                f"""
                Exception occurred while attempting to retrieve a document in MongoDB.
                Exception raised: {e}
                """
            )

        if switch_entry is None:
            raise SwitchDocumentNotFound

    def bulk_update(self, changes: list):
        self._switch_collection.bulk_write(changes)

    def dump_ids(self):
        return {collection['name']: collection["_id"] for collection in self._switch_collection.find()}

    def drop_database(self):
        if self._MongoConnector is not None and "switches" in self._network_state_db.list_collection_names():
            self._MongoConnector.drop_database("topology")

    def dump_network_db(self) -> dict:

        dumped_db = {}
        for collection in self._switch_collection.find():
            del collection["_id"]
            dumped_db[collection["name"]] = collection

        return dumped_db
