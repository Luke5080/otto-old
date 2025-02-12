from abc import ABC, abstractmethod


class AgentBase(ABC):

    @abstractmethod
    @property
    def agent_prompt(self):
        pass

    @abstractmethod
    @property
    def agent_prompt_template(self):
        pass

    @abstractmethod
    @property
    def agent_tools(self):
        pass

    @abstractmethod
    @property
    def agent_tool_descriptions(self):
        pass

    @abstractmethod
    def create_agent(self):
        pass
