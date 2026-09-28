"""LangChain tools wrapping the AOTrust notary API.

Every tool docstring doubles as the LLM-facing tool description — keep it
actionable for agents: what it does, what it returns, when to use it.

All sync tools bridge into the SDK's asyncio-native client via
``langchain_aotrust._client.run_async`` (safe inside a running event loop —
a dedicated worker-thread loop is used there; see _client.run_async).
"""
import hashlib
from typing import Optional

from langchain_core.tools import tool

from ._client import get_client, run_async


@tool
def aotrust_notarize_free(artifact_text: str) -> str:
    """Notarize an AI artifact on AOTrust (free tier, no wallet required).

    Computes the SHA-256 work_hash of the artifact text and registers a
    free UNPAID PDR (proof-of-existence record, NEAR-anchored, Ed25519
    signed). Use this whenever an agent's output must be provably
    timestamped and tamper-evident. Returns a human-readable confirmation
    with the shield_id and job_id to verify later at
    https://verify.aotrust.link. Rate limited per IP (free tier)."""
    import hashlib

    work_hash = hashlib.sha256(artifact_text.encode("utf-8")).hexdigest()
    res = run_async(get_client().shield_free(work_hash))
    shield_id = res.get("shield_id", "n/a")
    job_id = res.get("job_id", "n/a")
    tier = res.get("tier", "free")
    return (
        f"Notarized (tier={tier}). shield_id={shield_id} job_id={job_id} "
        f"work_hash={work_hash} "
        f"Verify later at https://verify.aotrust.link or with aotrust_verify(job_id)."
    )


@tool
def aotrust_verify(job_id: str) -> str:
    """Verify a previously notarized artifact on AOTrust by job_id.

    Fetches the PDR for the given job_id and runs full cryptographic
    verification (Ed25519 signature, Merkle inclusion, NEAR anchoring).
    Returns validity (true/false), the payment_anchor_type and whether the
    record is anchored on-chain. Use after aotrust_notarize_free or when a
    user supplies a job_id to prove a record exists."""
    pdr = run_async(get_client().get_pdr(job_id))
    v = run_async(get_client().verify_pdr(pdr.pdr_b64))
    valid = v.get("valid")
    if valid is None:
        valid = v.get("tx_verified_on_chain") is not None and v.get("sig_valid", False)
    pat = v.get("payment_anchor_type") or pdr.payment_anchor_type
    return (
        f"Verification for job_id={job_id}: valid={valid}, "
        f"payment_anchor_type={pat}, anchored status fetched, "
        f"verify_url={pdr.verify_url or 'https://verify.aotrust.link'}"
    )


@tool
def aotrust_status(job_id: str) -> str:
    """Check the notarization status of a job_id on AOTrust.

    Returns the current pipeline status (queued/anchored/etc.), whether the
    record is already anchored on NEAR, and the anchoring timestamp when
    available. Cheaper than aotrust_verify — use it to poll progress."""
    st = run_async(get_client().get_status(job_id))
    anchored = "yes" if st.is_anchored else "no"
    ts = getattr(st, "payment_hash", None) or ""
    return f"Status for job_id={job_id}: status={st.status}, anchored={anchored}, payment_hash={ts}"


# ── plain async variants (NOT @tool) — for LangGraph async agents ──────────

async def aotrust_notarize_free_async(artifact_text: str) -> str:
    """Async counterpart of aotrust_notarize_free (await directly in async agents)."""
    import hashlib

    work_hash = hashlib.sha256(artifact_text.encode("utf-8")).hexdigest()
    res = await get_client().shield_free(work_hash)
    shield_id = res.get("shield_id", "n/a")
    job_id = res.get("job_id", "n/a")
    tier = res.get("tier", "free")
    return (
        f"Notarized (tier={tier}). shield_id={shield_id} job_id={job_id} "
        f"work_hash={work_hash} "
        f"Verify later at https://verify.aotrust.link or with aotrust_verify(job_id)."
    )


async def aotrust_verify_async(job_id: str) -> str:
    """Async counterpart of aotrust_verify (await directly in async agents)."""
    pdr = await get_client().get_pdr(job_id)
    v = await get_client().verify_pdr(pdr.pdr_b64)
    valid = v.get("valid")
    if valid is None:
        valid = v.get("tx_verified_on_chain") is not None and v.get("sig_valid", False)
    pat = v.get("payment_anchor_type") or pdr.payment_anchor_type
    return (
        f"Verification for job_id={job_id}: valid={valid}, "
        f"payment_anchor_type={pat}, anchored status fetched, "
        f"verify_url={pdr.verify_url or 'https://verify.aotrust.link'}"
    )


async def aotrust_status_async(job_id: str) -> str:
    """Async counterpart of aotrust_status (await directly in async agents)."""
    st = await get_client().get_status(job_id)
    anchored = "yes" if st.is_anchored else "no"
    ts = getattr(st, "payment_hash", None) or ""
    return f"Status for job_id={job_id}: status={st.status}, anchored={anchored}, payment_hash={ts}"