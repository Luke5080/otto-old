from typing import Optional

from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import \
    create_tool_list


class IntentProcessorPool:
    _model_fetcher: ModelFactory

    def __init__(self, size: Optional[int] = 6,
                 models: Optional[list[str]] = ["gpt-4o", "deepseek"]):
        self.pool = []
        self._models = models
        self._pool_size = size
        self._model_fetcher = ModelFactory()
        self._create_pool()

    def _create_pool(self):
        """
        Method to create object pool of size set in pool attribute and create pool with
        models specified in models attribute
        """

        # if pool size % length of model list != 0, then the pool size will be automatically scaled down
        # I have no ideas what do to do otherwise without adding some extra complexity to this class
        model_distribution = self._pool_size // len(self._models)

        for i in range(len(self._models)):
            model = self._model_fetcher.get_model(self._models[i])
            for _ in range(model_distribution):
                self.pool.append(IntentProcessor(model, create_tool_list(), intent_processor_prompt))

    def get_intent_processor(self, model_required: str) -> IntentProcessor:
        """
        Method to get an IntentProcessor instance from object pool. If IntentProcessor with required
        model does not exist in the current pool, create a new instance of IntentProcessor
        and return it
        Args:
            model_required: str - LLM to be used with IntentProcessor
        """

        if self.pool and any(p.model_name == model_required for p in self.pool):
            designated_processor = next(p for p in self.pool if p.model_name == model_required)

            print(f"found p {designated_processor}")

            return designated_processor
        else:
            print(f"No IntentProcessor instance found which utilises model {model_required}. Creating new instance")

            # remove last element of pool as we are creating a new instance, which will appended to the pool
            # once intent fulfilment operation is done. This needs to be done to keep pool size to the required
            # size specified during initialisation
            self.pool.pop()

            return IntentProcessor(self._model_fetcher.get_model(model_required), create_tool_list(),
                                   intent_processor_prompt)

    def return_intent_processor(self, processor: IntentProcessor):
        """
        Method to return IntentProcessor instance to object pool once intent fulfilment operation
        is complete.
        Args:
             processor: IntentProcessor - instance to be returned to the pool
        """
        self.pool.append(processor)
