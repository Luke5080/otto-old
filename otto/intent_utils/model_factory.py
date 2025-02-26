from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

class ModelFactory:
    @staticmethod
    def get_model(model):
        match model:
            case "gpt-4o-mini":
                return ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
            case "gpt-4o":
                return ChatOpenAI(model_name="gpt-4o", temperature=0)

            case "llama":
                 return ChatGroq(model="qwen-2.5-32b", temperature=0)
