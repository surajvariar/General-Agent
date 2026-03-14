from models.settings import settings
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


class ModelProvider:
    def __init__(self, model_name: str, temp: int = 0.5):
        self.model_name = model_name
        self.temp = temp
        self.BASE_URL = settings.BASE_URL

    def get_provider_instance(self):
        if settings.OPENAI_API_KEY:
            provider = ChatOpenAI(
                model=self.model_name, base_url=self.BASE_URL, temperature=self.temp
            )
        if settings.OLLAMA_API_KEY:
            provider = ChatOllama(
                model=self.model_name, base_url=self.BASE_URL, temperature=self.temp
            )
        if settings.HUGGINGFACEHUB_API_TOKEN:
            llm = HuggingFaceEndpoint(
                repo_id=self.model_name,
                temperature=self.temp
            )
            provider=ChatHuggingFace(llm=llm)

        return provider
