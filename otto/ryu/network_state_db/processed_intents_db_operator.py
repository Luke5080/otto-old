from datetime import datetime, timedelta

from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import Session, joinedload

from otto.api.models.called_tools import CalledTools
from otto.api.models.entities import Entities
from otto.api.models.processed_intents import ProcessedIntents
from otto.api.models.tool_calls import ToolCalls


class ProcessedIntentsDbOperator:
    def __init__(self):
        self._engine = create_engine("mysql+pymysql://root:root@127.0.0.1:3306/authentication_db")
        self._session = Session(self._engine)

    def save_intent(self, agent_run: str, username: str, intent: str, timestamp: datetime,
                    called_tools: list[dict], model: str) -> None:
        """
        Args:
            agent_run: ID of the agent run
            username: Username of the user/app
            intent: The intent declared
            timestamp: datetime object
            called_tools: List of completed operations carried out by IntentProcessor

        """

        target_id = self._session.query(Entities.id).filter(Entities.username == username).scalar()

        if target_id is None:
            raise Exception("Cannot find User")

        processed_intent = ProcessedIntents(
            agent_run=agent_run,
            declared_by_id=target_id,
            intent=intent,
            timestamp=timestamp,
            model=model
        )

        self._session.add(processed_intent)

        for i in range(len(called_tools)):
            for tool_name, args in called_tools[i].items():
                tool_call_id = self._session.query(ToolCalls.id).filter(ToolCalls.name == tool_name).scalar()

                processed_intent_tool_call = CalledTools(
                    agent_run=agent_run,
                    run_order=i + 1,
                    tool_call_id=tool_call_id,
                    arguments=args
                )

                self._session.add(processed_intent_tool_call)

        self._session.commit()

    def get_latest_activity(self) -> dict:
        """
        Method to find up to the 5 most recent intents declared and registered in the ProcessedIntents table.
        The found value is returned and to be used in the /get-latest-activity API call.
        """
        last_five_intents = (
            self._session.query(ProcessedIntents)
            .options(joinedload(ProcessedIntents.declared_user))
            .options(joinedload(ProcessedIntents.outcomes))
            .order_by(desc(ProcessedIntents.timestamp))
            .limit(5)
            .all()
        )

        response = {}

        for index, intent in enumerate(last_five_intents):
            response[str(index)] = {
                "intent": intent.intent,
                "declaredBy": intent.declared_user.username,
                "outcome": [f"{tool_call.name}({tool_call.args})" for tool_call in intent.outcomes]
            }

        return response

    def get_weekly_activity(self) -> dict:
        """
        Method to find the count of intents declared between one week from/to the current date.
        The found value is returned and to be used in the /get-weekly-activity API call.
        """

        end_date = datetime.today() + timedelta(days=1)
        one_week_ago = end_date - timedelta(weeks=1)

        results = (
            self._session.query(
                func.date(ProcessedIntents.timestamp).label("intent_date"),
                func.count().label("intent_count")
            )
            .filter(ProcessedIntents.timestamp.between(one_week_ago, end_date))
            .group_by(func.date(ProcessedIntents.timestamp))
            .order_by("intent_date")
            .all()
        )

        intent_count_by_date = {
            intent_date: intent_count for intent_date, intent_count in results
        }

        response = {
            (one_week_ago + timedelta(days=i)).isoformat(): intent_count_by_date.get(one_week_ago + timedelta(days=i),
                                                                                     0)
            for i in range(7)
        }

        return response

    def get_top_activity(self) -> dict:
        """
        Method to find the amount of intents declared per user and returned in descending order.
        The found value is returned and to be used in the /get-top-activity API call.
        """
        top_activity = (
            self._session.query(
                Entities.username,
                func.count(ProcessedIntents.agent_run).label('count')
            )
            .join(ProcessedIntents, Entities.id == ProcessedIntents.declared_by_id)
            .group_by(Entities.username)
            .order_by(desc('count'))
            .all()
        )

        response = {username: count for username, count in top_activity}

        return response

    def get_model_usage(self) -> dict:

        model_usage = (
            self._session.query(ProcessedIntents.model, func.count().label('count'))
            .group_by(ProcessedIntents.model)
            .order_by(desc('count'))
            .all()
        )

        response = {model: count for model, count in model_usage}

        return response
