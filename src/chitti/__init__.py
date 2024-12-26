"""Chitti - AI agent ecosystem"""

from .hookspecs import AgentSpec, ModelProviderSpec, PromptRequest, PromptResponse
from .manager import PluginManager

__all__ = [
    "AgentSpec",
    "ModelProviderSpec",
    "PromptRequest",
    "PromptResponse",
    "PluginManager"
]
