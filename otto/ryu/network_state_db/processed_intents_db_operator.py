from pymongo import MongoClient
from exceptions import ProcessedIntentsDbException

class ProcessedIntentsDbOperator:

      __instance = None

      @staticmethod
      def get_instance():
          if ProcessedIntentsDbOperator.__instance is None:
             ProcessedIntentsDbOperator()
          return ProcessedIntentsDbOperator.__instance

      def __init__(self):
          if ProcessedIntentsDbOperator.__instance is None:
             self.mongo_connector = MongoClient('localhost', 27018)
             self.database = self.mongo_connector['intent_history']
             self.collection = self.database['processed_intents']

             ProcessedIntentsDbOperator.__instance = self

          else:
            raise Exception(f"An occurence of ProcessedIntentsDbOperator exists at {ProcessedIntentsDbOperator.__instance}")

      def save_intent(self, context:str, intent:str, operations:list[str], timestamp: str) -> dict:
            processed_intent = {
                "declaredBy": context,
                "intent": intent,
                "outcome": operations,
                "timestamp": timestamp
            }
            try:

               self.collection.insert_one(processed_intent)

            except PyMongoError as e:
                   raise ProcessedIntentsDbException(
                   f"Error while putting processed_intent into otto_processed_intents_db: {e}")

            print(processed_intent)
            return processed_intent
