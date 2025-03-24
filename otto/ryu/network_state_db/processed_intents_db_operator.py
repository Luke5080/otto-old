from datetime import datetime, timedelta
from typing import Union

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from exceptions import ProcessedIntentsDbException


class ProcessedIntentsDbOperator:
    mongo_connector: Union[None, MongoClient]

    def __init__(self):
        self.mongo_connector = None
        self.database = None

    def connect(self):
        """
        Connect method to be used when wishing to connect to the intent_history database.
        This is run after the object has been created, and created within the process which will
        connect to the database to prevent any forking issues.
        """
        if self.mongo_connector is None:
            self.mongo_connector = MongoClient('localhost', 27018)

            self.database = self.mongo_connector['intent_history']

    def save_intent(self, intent: str, context: str, operations: list[str], timestamp: datetime) -> dict:
        """
        Args:
            intent: The intent declared
            context: User/Application name
            operations: List of completed operations carried out by IntentProcessor
            timestamp: datetime object

        Method to save the processed intent to the processed_intents collection in intents_history database
        """
        collection = self.database['processed_intents']
        processed_intent = {
            "declaredBy": context,
            "intent": intent,
            "outcome": operations,
            "timestamp": timestamp
        }
        try:

            collection.insert_one(processed_intent)

        except PyMongoError as e:
            raise ProcessedIntentsDbException(
                f"Error while putting processed_intent into otto_processed_intents_db: {e}")

        return processed_intent

    def get_latest_activity(self) -> dict:
        collection = self.database['processed_intents']
        try:

            latest_data = collection.find().sort('_id', -1).limit(5)

            response = {}

            for record in latest_data:
                response[str(record['timestamp'])] = {}
                response[str(record['timestamp'])]['declaredBy'] = record['declaredBy']
                response[str(record['timestamp'])]['intent'] = record['intent']
                response[str(record['timestamp'])]['outcome'] = record['outcome']


        except PyMongoError as e:
            raise ProcessedIntentsDbException(
                f"Error while attempting to achieve latest data: {e}")

        return response

    def get_weekly_activity(self) -> dict:
        collection = self.database['processed_intents']
        today = datetime.today()
        one_week_ago = today - timedelta(weeks=1)

        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": one_week_ago, "$lt": today}
                }
            },
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}]

        response = {}

        results = list(collection.aggregate(pipeline))

        for result in results:
            response[result['_id']] = result['count']

        return response

    def get_top_activity(self) -> dict:
        collection = self.database['processed_intents']
        pipeline = [
            {
                "$group": {
                    "_id": "$declaredBy", "count": {"$sum": 1}}
            },
            {"$sort": {"count": -1}}]

        response = {}

        results = list(collection.aggregate(pipeline))

        for result in results:
            response[result['_id']] = result['count']

        return response

    def register_model_usage(self, model: str) -> dict:
        collection = self.database['model_usage']

        collection.update_one({ 'model' : model}, { '$inc': {'count': 1} }, upsert=True)

    def get_model_usage(self) -> dict:
        collection = self.database['model_usage']

        model_usage = {}
        for col in collection.find():
            del col['_id']
            model_usage[col['model']] = col['count']

        return model_usage
        
