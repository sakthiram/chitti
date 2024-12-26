"""Chitti - AI agent ecosystem"""

from .hookspecs import AgentSpec, ModelProviderSpec, PromptRequest, PromptResponse
from .base import BaseAgent, BasePromptPlugin

__all__ = [
    'AgentSpec',
    'ModelProviderSpec',
    'PromptRequest',
    'PromptResponse',
    'BaseAgent',
    'BasePromptPlugin'
]
