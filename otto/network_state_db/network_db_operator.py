from pymongo import MongoClient
from exceptions import NetworkDatabaseException, SwitchDocumentNotFound, MultipleNetworkDbOperators
from pymongo.errors import PyMongoError

class NetworkDbOperator:
    _MongoConnector : MongoClient
    object_ids : dict

    __instance = None

    @staticmethod
    def get_instance():
        if NetworkDbOperator.__instance is None:
            NetworkDbOperator()
        return NetworkDbOperator.__instance



    def __init__(self):
        if NetworkDbOperator.__instance is None:
           self._MongoConnector = MongoClient('localhost', 27017)
           self._network_state_db = self._MongoConnector["topology"]
           self._switch_collection = self._network_state_db["switches"]
           self.object_ids = {}

           NetworkDbOperator.__instance = self

        else:
            raise MultipleNetworkDbOperators(
                f"An instance of NetworkDbOperator already exists at {NetworkDbOperator.__instance}"
                )

    def put_switch_to_db(self, switch_struct: dict) -> None:
        try:
            inserted_doc = self._switch_collection.insert_one(switch_struct)
            print(inserted_doc.inserted_id)
            self.object_ids[switch_struct["name"]] = inserted_doc.inserted_id

        except PyMongoError as e:
            raise NetworkDatabaseException(
                f"""
                Exception occurred while attempting to put a document into MongoDB.
                Exception raised: {e}
                """
            )

        except Exception as e:
            raise NetworkDatabaseException(e)

    def modify_switch_document(self, switch_dpid: str, change:dict) -> None:

        match_exp = { '_id' : self.object_ids[switch_dpid] }

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
            self._switch_collection.delete_one({"_id" : self.object_ids[switch_dpid]})
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
            match = {"_id" : self.object_ids[switch_dpid]}

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

    def dump_network_db(self):
        dumped_db = {}
        for collection in self._switch_collection.find():
            del collection["_id"]
            dumped_db[collection["name"]] = collection

        return dumped_db
