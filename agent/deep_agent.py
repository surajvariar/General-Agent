from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
load_dotenv(verbose=True)

class Agents():
    def __init__(self,model_name:str):
        self.model_name=model_name
        self.OLLAMA_URL="https://ollama.com"
        self.SYSTEM_INSTRUCTIONS="""You are an expert researcher. Research on a given topic and provide a detailed analysis on the same."""
    def config_agent(self):
        self.agent=create_deep_agent(
            model=self._init_model(),
            system_prompt=self.SYSTEM_INSTRUCTIONS
        )
    def _init_model(self):
        self.model=ChatOllama(
            model=self.model_name,
            base_url=self.OLLAMA_URL,
            temperature=0.5
        )
        return self.model
    def get_agent(self):
        return self.agent