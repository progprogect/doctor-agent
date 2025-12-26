"""Base tool class for LangChain tools."""

from abc import ABC, abstractmethod
from typing import Optional

from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base input for tools."""

    pass


class BaseAgentTool(BaseTool, ABC):
    """Base class for agent tools."""

    name: str
    description: str
    agent_id: Optional[str] = None

    def __init__(self, agent_id: Optional[str] = None, **kwargs):
        """Initialize tool."""
        # Set agent_id in kwargs so Pydantic can validate it
        if agent_id is not None:
            kwargs['agent_id'] = agent_id
        super().__init__(**kwargs)

    @abstractmethod
    async def _arun(self, *args, **kwargs):
        """Async run method."""
        pass

    @abstractmethod
    def _run(self, *args, **kwargs):
        """Sync run method."""
        pass




