from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from agent.tools import internet_search
from dotenv import load_dotenv
load_dotenv(verbose=True)

class Agents():
    def __init__(self,model_name:str):
        self.model_name=model_name
        self.OLLAMA_URL="https://ollama.com"
        self.SYSTEM_INSTRUCTIONS="""You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""
    def config_agent(self):
        self.agent=create_deep_agent(
            model=self._init_model(),
            tools=[internet_search],
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
        self.config_agent()
        return self.agent