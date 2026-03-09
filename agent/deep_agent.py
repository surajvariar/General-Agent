from deepagents import create_deep_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from agent.tools import internet_search
from langchain.agents.middleware import ToolCallLimitMiddleware
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv
import os
load_dotenv(verbose=True)


class Agents:
    def __init__(self, model_name: str,temp:int=0.5):
        self.model_name = model_name
        self.BASE_URL = os.getenv("BASE_URL") 
        self.temp=temp
        self.SYSTEM_INSTRUCTIONS = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

## Tools Available

### `internet_search`
Run web searches. Use for gathering information. Specify `max_results`, `topic` ("general", "news", "finance"), and `include_raw_content`.

### Filesystem Tools (use actively for large outputs)
- `ls`: List files
- `read_file`: Read file content  
- `write_file`: Save research/notes
- `edit_file`: Update existing files

**Storage guide:**
- **Ephemeral** (current session): `/notes.txt`, `/research/`, `/workspace/`
- **Persistent** (across conversations): `/memories/user-preferences.txt`, `/memories/research-summary.txt`

### Planning
Use `write_todos` to break down complex research into steps.

## Research Process
1. Plan with `write_todos`
2. Search with `internet_search` 
3. Save large results: `write_file("/notes/search-results.txt", ...)` 
4. Analyze and synthesize in `/workspace/report.md`
5. Save key findings: `write_file("/memories/[topic]-summary.txt", ...)` for future reference

Write concise, structured final reports."""

    def get_agent(self):
        agent = create_deep_agent(
            model=self._init_model(),
            tools=[internet_search],
            system_prompt=self.SYSTEM_INSTRUCTIONS,
            middleware=[
                # Global limit
                ToolCallLimitMiddleware(thread_limit=20, run_limit=10),
                # Tool-specific limit
                ToolCallLimitMiddleware(
                    tool_name="internet_search",
                    thread_limit=5,
                    run_limit=3,
                ),
            ],
            backend=self.make_backend,
            store=InMemoryStore(),
            checkpointer=MemorySaver()
        )
        return agent
    
    def make_backend(self,runtime):
        return CompositeBackend(
            default=StateBackend(runtime),
            routes={
                "/memories/": StoreBackend(runtime)
            }
        )

    def _init_model(self):
        if os.getenv("OLLAMA_API_KEY"):
            if self.model_name=="":
                self.model_name="gpt-oss:20b"
            model = ChatOllama(
                model=self.model_name, base_url=self.BASE_URL, temperature=self.temp
            )
        elif os.getenv("OPENAI_API_KEY"):
            if self.model_name=="":
                self.model_name="openai/gpt-oss-20b:free"
            model=ChatOpenAI(model=self.model_name,base_url=self.BASE_URL,temperature=self.temp)
        return model
