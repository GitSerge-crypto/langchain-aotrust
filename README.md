# langchain-aotrust

<!-- mcp-name: link.aotrust/notary -->

LangChain tools for **AOTrust** notarization — cryptographic
proof-of-existence for AI agent outputs. Free tier (no wallet required),
PDRs signed with Ed25519, Merkle-included and anchored on NEAR.

Works with any agent built on `langchain-core` (LangChain, LangGraph,
CrewAI via the standard BaseTool interface, pydantic-ai adapters).

## Install

```bash
pip install langchain-aotrust
```

## Quickstart

```python
from langchain_aotrust import (
    aotrust_notarize_free,
    aotrust_verify,
    aotrust_status,
)

# 1. Notarize an artifact (free tier — no API key, no wallet)
print(aotrust_notarize_free.invoke({"artifact_text": "analysis v3: portfolio risk moderate"}))
# Notarized (tier=free). shield_id=9f2c... job_id=7a1b... work_hash=...
# Verify later at https://verify.aotrust.link or with aotrust_verify(job_id).

# 2. Check pipeline status
print(aotrust_status.invoke({"job_id": "<job_id>"}))
# Status for job_id=7a1b...: status=anchored, anchored=yes, payment_hash=...

# 3. Full cryptographic verification
print(aotrust_verify.invoke({"job_id": "<job_id>"}))
# Verification for job_id=7a1b...: valid=True, payment_anchor_type=0, ...
```

Wiring into a LangChain agent:

```python
from langchain_aotrust import aotrust_notarize_free, aotrust_verify
from langchain.agents import create_tool_calling_agent  # any agent works

tools = [aotrust_notarize_free, aotrust_verify, aotrust_status]
```

Async agents (LangGraph) can await the plain functions directly:

```python
from langchain_aotrust import aotrust_notarize_free_async
result = await aotrust_notarize_free_async(artifact_text="...")
```

Configuration (optional — defaults to the public endpoint):

```python
from langchain_aotrust import configure
configure(base_url="https://api.aotrust.link")  # NO /v1 suffix — the SDK appends paths
```

## What the proofs mean

| Horizon | Guarantee |
|---|---|
| **Instant** | SHA-256 work_hash bound into a signed PDR (Ed25519, notary key) — tamper-evident from notarization time |
| **Python** | PDR bytes verifiable offline by anyone with the notary public key |
| **Forever** | Daily Merkle root anchored on NEAR blockchain — proof survives even if the service disappears |

## Free tier

- No API key, no wallet, no payment.
- Rate limited per IP (5 notarizations / 24h) — paid x402 tier ($0.01) in a
  future release for higher throughput.

## Links

- Docs: https://docs.aotrust.link
- Live verifier: https://verify.aotrust.link
- SDK: https://pypi.org/project/aotrust-protocol/

## License

MIT
## Anchored release

**This release is anchored:** [Shield ID `5558f228`](https://verify.aotrust.link/s/5558f228) - the published sdist
of version `0.1.1` has a public first record in the AOTrust log (Ed25519-signed receipt, Merkle root
committed hourly to NEAR). Verify it without trusting us, or check the whole log with the
[exit kit](https://docs.aotrust.link/exit-kit.html).
