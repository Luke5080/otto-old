from typing import Union

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from exceptions import (NetworkDatabaseException,
                        SwitchDocumentNotFound)


class NetworkDbOperator:
    _MongoConnector: Union[None, MongoClient]

    def __init__(self):
        self._MongoConnector = None
        self._network_state_db = None
        self._switch_collection = None

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
        if self._MongoConnector is not None and "topology" in self._database.collection_names():
           self._MongoConnector.drop_database('topology')

    def dump_network_db(self) -> dict:

        dumped_db = {}
        for collection in self._switch_collection.find():
            del collection["_id"]
            dumped_db[collection["name"]] = collection

        return dumped_db
