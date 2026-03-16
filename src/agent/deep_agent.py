from deepagents import create_deep_agent
from agent.tools import get_tavily_mcp, think_tool
from langchain.agents.middleware import ToolCallLimitMiddleware, ToolRetryMiddleware
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from models.provider import ModelProvider
from prompts.system_prompts import *


class Agents:
    def __init__(self, model_name: str, temp: int = 0.5):
        self.provider = ModelProvider(model_name, temp)
        self.tavily_tools = None

    @classmethod
    async def create(cls, model_name: str, temp: int = 0.5):
        instance = cls(model_name, temp)
        instance.tavily_tools = await get_tavily_mcp()
        return instance

    def get_agent(self):

        research_subagent = {
            "name": "research-agent",
            "description": (
                "Conducts in-depth, multi-source research requiring 5+ searches, "
                "synthesis, and structured reports. Use for comprehensive research tasks, "
                "not single lookups."
            ),
            "system_prompt": RESEARCH_SUBAGENT_PROMPT,
            "tools": [*self.tavily_tools, think_tool],
            # Higher limits — research is iterative
            "middleware": [
                ToolCallLimitMiddleware(thread_limit=40, run_limit=20),
                ToolRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                ),
            ],
        }

        agent = create_deep_agent(
            model=self.provider.get_provider_instance(),
            tools=[*self.tavily_tools, think_tool],
            subagents=[research_subagent],
            system_prompt=MAIN_AGENT_PROMPT,
            middleware=[
                # Global limit
                ToolCallLimitMiddleware(thread_limit=20, run_limit=10),
                ToolRetryMiddleware(
                    max_retries=3,
                    backoff_factor=2.0,
                    initial_delay=1.0,
                ),
            ],
            backend=self.make_backend,
            store=InMemoryStore(),
            checkpointer=MemorySaver(),
        )
        return agent

    def make_backend(self, runtime):
        return CompositeBackend(
            default=StateBackend(runtime), routes={"/memories/": StoreBackend(runtime)}
        )
