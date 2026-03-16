from models.settings import settings
from typing import Literal
from tavily import TavilyClient
from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_tavily_mcp():
    tavily_mcp_client = MultiServerMCPClient(
        {
            "tavily-remote": {
                "transport": "http",
                "url": f"https://mcp.tavily.com/mcp?tavilyApiKey={settings.TAVILY_API_KEY.get_secret_value()}",
                "headers": {
                    "Authorization": settings.TAVILY_API_KEY.get_secret_value(),
                },
            }
        }
    )
    tavily_tools = await tavily_mcp_client.get_tools()
    return tavily_tools


tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


def think_tool(thought: str) -> str:
    """A scratchpad for reasoning before acting.

    Use this tool whenever you need to reason through something before taking
    an action or producing output. It creates no side effects — the thought is
    not sent anywhere, executed, or stored. It is a private reasoning step.

    Use it before:
    - Choosing between tool calls or approaches
    - Interpreting ambiguous instructions
    - Checking your own logic or assumptions
    - Deciding whether you have enough information to proceed
    - Planning a multi-step sequence of actions

    The thought can be structured or free-form — whatever matches the
    complexity of the situation. There is no required format.

    Args:
        thought: Your reasoning. Can be a quick sanity check or a detailed
                 analysis. Write for yourself, not for the user.

    Returns:
        The thought, unchanged. This confirms it was recorded so you can
        reference it in subsequent steps.
    """
    return thought
