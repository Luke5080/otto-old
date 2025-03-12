from otto.intent_utils.agent_prompt import intent_processor_prompt
from otto.intent_utils.model_factory import ModelFactory
from otto.ryu.intent_engine.intent_processor_agent import IntentProcessor
from otto.ryu.intent_engine.intent_processor_agent_tools import \
    create_tool_list


class IntentProcessorPool:
    _model_fetcher: ModelFactory

    def __init__(self):
        self.pool = []
        self._model_fetcher = ModelFactory()
        self._create_pool()

    def _create_pool(self):
        llm = self._model_fetcher.get_model("gpt-4o")
        for i in range(3):
            self.pool.append(IntentProcessor(llm, create_tool_list(), intent_processor_prompt))

        llm = self._model_fetcher.get_model("deepseek")
        for i in range(3):
            self.pool.append(IntentProcessor(llm, create_tool_list(), intent_processor_prompt))

    def get_intent_processor(self, model_required: str) -> IntentProcessor:
        if self.pool and any(p.model_name == model_required for p in self.pool):
            x = next(p for p in self.pool if p.model_name == model_required)
            print(f"found p {x}")
            return x
        else:
            print("no p found")
            return IntentProcessor(self._model_fetcher.get_model(model_required), create_tool_list(),
                                   intent_processor_prompt)

    def return_intent_processor(self, processor: IntentProcessor):
        self.pool.append(processor)
