"""langchain-aotrust — LangChain tools for AOTrust notarization.

Cryptographic proof-of-existence for AI agent outputs: free-tier notarization
(SHA-256 work_hash -> PDR, NEAR-anchored) and public verification, exposed
as LangChain BaseTool instances compatible with any agent built on
langchain-core (LangChain, LangGraph, CrewAI, pydantic-ai via the standard
BaseTool interface).
"""

__version__ = "0.1.0"

from ._client import get_client, configure, reset_client
from .tools import (
    aotrust_notarize_free,
    aotrust_verify,
    aotrust_status,
    aotrust_notarize_free_async,
    aotrust_verify_async,
    aotrust_status_async,
)

__all__ = [
    "__version__",
    "get_client",
    "configure",
    "reset_client",
    "aotrust_notarize_free",
    "aotrust_verify",
    "aotrust_status",
    "aotrust_notarize_free_async",
    "aotrust_verify_async",
    "aotrust_status_async",
]