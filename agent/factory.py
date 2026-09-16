"""Factory for the SmartB100 deep agent (deepagents + Groq), isolated behind agent/."""

from typing import cast

from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from pydantic import SecretStr

from agent.prompt import AGENT_INSTRUCTIONS
from agent.tools import search_corpus
from core.config import settings
from core.schemas import AgentGraph


def default_model() -> ChatGroq:
    """Build the default hosted Groq chat model for the agent path.

    Returns:
        ``ChatGroq`` configured with ``settings.agent_model`` and the optional
        Groq API key.
    """
    api_key = SecretStr(settings.groq_api_key) if settings.groq_api_key is not None else None
    return ChatGroq(model=settings.agent_model, api_key=api_key)


def create_agent(model: BaseChatModel | None = None) -> AgentGraph:
    """Build the compiled deep-agent graph.

    Args:
        model: Optional LangChain chat model. When omitted, a Groq model is
            built from settings; tests can inject a stub to avoid network calls.

    Returns:
        Compiled DeepAgents graph implementing the ``AgentGraph`` protocol.
    """
    if model is None:
        model = default_model()
    return cast(
        AgentGraph,
        create_deep_agent(
            model=model,
            tools=[search_corpus],
            system_prompt=AGENT_INSTRUCTIONS,
        ),
    )
