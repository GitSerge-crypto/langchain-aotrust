"""test_live.py — live smoke against https://api.aotrust.link.

Excluded from the default run (pyproject addopts -m 'not live').
Run explicitly: pytest -m live
"""
import hashlib
import os

import pytest

from langchain_aotrust import (
    aotrust_notarize_free,
    aotrust_status,
)
import langchain_aotrust._client as client_mod


@pytest.mark.live
def test_live_notarize_free_roundtrip():
    fake = client_mod._client
    try:
        client_mod._client = None  # force the real singleton
        artifact = f"langchain-aotrust live smoke {os.urandom(4).hex()}"
        out = aotrust_notarize_free.invoke({"artifact_text": artifact})
        assert "shield_id=" in out
        assert "job_id=" in out
        # extract job_id and check status
        job_id = out.split("job_id=")[1].split(" ")[0].strip()
        status_out = aotrust_status.invoke({"job_id": job_id})
        assert "status=" in status_out
    finally:
        client_mod._client = fake


@pytest.mark.live
def test_live_free_tier_shape():
    import asyncio
    from langchain_aotrust import get_client

    work_hash = hashlib.sha256(b"langchain-aotrust live shape probe").hexdigest()
    res = asyncio.run(get_client().shield_free(work_hash))
    assert isinstance(res, dict)
    assert "shield_id" in res
    assert "job_id" in res
    assert res.get("tier") in ("free", None)