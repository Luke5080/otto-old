from datetime import datetime, timedelta

from otto.api.authentication_db import authentication_db
from otto.api.models.called_tools import CalledTools
from otto.api.models.processed_intents import ProcessedIntents
from otto.api.models.entities import Entities

from otto.exceptions import ProcessedIntentsDbException


class ProcessedIntentsDbOperator:

    @staticmethod
    def save_intent(agent_run: str, username: str, intent: str, timestamp: datetime,
                    called_tools: list[dict]) -> None:
        """
        Args:
            agent_run: ID of the agent run
            username: Username of the user/app
            intent: The intent declared
            timestamp: datetime object
            called_tools: List of completed operations carried out by IntentProcessor

        """

        target_id = Entities.query.with_entities(Entities.id).filter_by(username=username).scalar()

        if target_id is None:
            raise Exception("Cannot find User")

        processed_intent = ProcessedIntents(
            agent_run=agent_run,
            declared_by_id=target_id,
            intent=intent,
            timestamp=timestamp
        )

        authentication_db.session.add(processed_intent)

        for i in range(len(called_tools)):
            for tool_name, args in called_tools[i].items():
                tool_call_id = CalledTools.query.with_entities(CalledTools.id).filter_by(name=tool_name).scalar()
                processed_intent_tool_call = CalledTools(
                    agent_run=agent_run,
                    run_order=i+1,
                    tool_call_id=tool_call_id,
                    arguments=args
                )

                authentication_db.session.add(processed_intent_tool_call)

        authentication_db.session.commit()

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

        collection.update_one({'model': model}, {'$inc': {'count': 1}}, upsert=True)

    def get_model_usage(self) -> dict:
        collection = self.database['model_usage']

        model_usage = {}
        for col in collection.find():
            del col['_id']
            model_usage[col['model']] = col['count']

        return model_usage
