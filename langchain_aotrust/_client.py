"""Client singleton + sync/async bridge for langchain-aotrust.

URL contract: the AOTrust NotaryClient assembles full endpoint paths itself
(``/v1/shield/free``, ``/v1/status/{job_id}``, ...) — the ``base_url`` must
NEVER include a trailing ``/v1`` segment. Passing ``https://api.aotrust.link/v1``
would produce double-prefixed ``/v1/v1/...`` requests (the bug recorded in
examples/langchain_tool.py of aotrust-protocol).
"""
import asyncio
import concurrent.futures
from typing import Optional

from agent_notary import NotaryClient

DEFAULT_BASE_URL = "https://api.aotrust.link"

_client: Optional[NotaryClient] = None


def get_client() -> NotaryClient:
    """Lazy singleton of the async NotaryClient (aotrust-protocol)."""
    global _client
    if _client is None:
        # base_url default https://api.aotrust.link — WITHOUT a /v1 suffix
        _client = NotaryClient(base_url="https://api.aotrust.link")
    return _client


def configure(base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
    """Replace the singleton (call before first use, or use reset_client()).

    Args:
        base_url: API origin WITHOUT the /v1 path segment (e.g.
            https://api.aotrust.link or a testnet mirror).
        api_key: optional key for authenticated endpoints (quote channel).
    """
    global _client
    _client = NotaryClient(api_key=api_key, base_url=base_url)


def reset_client() -> None:
    """Drop the singleton (next get_client() re-creates it). Mainly for tests."""
    global _client
    _client = None


def run_async(coro):
    """Run a coroutine from sync code, safe inside a running event loop.

    LangChain agents invoke tools synchronously by default, but agents can
    also be driven from within an async application (LangGraph, Jupyter
    kernels). Plain ``asyncio.run()`` raises ``RuntimeError`` when a loop is
    already running, so this bridge detects a running loop and executes the
    coroutine on a dedicated worker thread with its own fresh loop.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()