"""test_tools.py — mock-based tests, NO network."""
import hashlib
import asyncio
import unittest
from unittest.mock import patch

from langchain_aotrust import (
    aotrust_notarize_free,
    aotrust_verify,
    aotrust_status,
    aotrust_notarize_free_async,
    aotrust_verify_async,
    aotrust_status_async,
)
import langchain_aotrust._client as client_mod


class _FakeClient:
    """Stands in for aotrust_protocol.NotaryClient — records base_url, no network."""

    def __init__(self):
        self.base_url = "https://api.aotrust.link"
        self.calls = []

    async def shield_free(self, work_hash):
        self.calls.append(("shield_free", work_hash))
        return {
            "status": "queued",
            "job_id": "job-123",
            "pdr_b64": "QUJD",
            "shield_id": "9f2c1a",
            "payment_anchor_type": 0,
            "tier": "free",
        }

    async def get_status(self, job_id):
        self.calls.append(("get_status", job_id))
        return asyncio.stub_status if False else _status_result()

    async def get_pdr(self, job_id):
        self.calls.append(("get_pdr", job_id))
        return _pdr_result()

    async def verify_pdr(self, pdr_b64):
        self.calls.append(("verify_pdr", pdr_b64))
        return {"valid": True, "payment_anchor_type": 0, "sig_valid": True}


def _status_result():
    from agent_notary import StatusResult
    return StatusResult(status="anchored", pdr_b64="QUJD", payment_hash="deadbeef")


def _pdr_result():
    from agent_notary import PdrResult
    return PdrResult(
        pdr_b64="QUJD",
        payment_hash="deadbeef",
        payment_anchor_type=0,
        verify_url="https://verify.aotrust.link/?pdr=QUJD",
    )


class TestNotarizeFree(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeClient()
        client_mod._client = self.fake

    def tearDown(self):
        client_mod._client = None

    def test_returns_string_with_shield_id(self):
        out = aotrust_notarize_free.invoke({"artifact_text": "hello world"})
        self.assertIsInstance(out, str)
        self.assertIn("shield_id=9f2c1a", out)
        self.assertIn("job_id=job-123", out)
        self.assertIn("verify.aotrust.link", out)

    def test_sha256_stable(self):
        expected = hashlib.sha256(b"hello world").hexdigest()
        aotrust_notarize_free.invoke({"artifact_text": "hello world"})
        self.assertEqual(self.fake.calls[0][1], expected)
        # determinism: same input -> same hash
        aotrust_notarize_free.invoke({"artifact_text": "hello world"})
        self.assertEqual(self.fake.calls[0][1], self.fake.calls[1][1])


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeClient()
        client_mod._client = self.fake

    def tearDown(self):
        client_mod._client = self.fake

    def test_parses_valid(self):
        out = aotrust_verify.invoke({"job_id": "job-123"})
        self.assertIn("valid=True", out)
        self.assertIn("payment_anchor_type=0", out)
        # get_pdr + verify_pdr both called
        names = [c[0] for c in self.fake.calls]
        self.assertIn("get_pdr", names)
        self.assertIn("verify_pdr", names)


class TestStatus(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeClient()
        client_mod._client = self.fake

    def tearDown(self):
        client_mod._client = self.fake

    def test_status_anchored(self):
        out = aotrust_status.invoke({"job_id": "job-123"})
        self.assertIn("status=anchored", out)
        self.assertIn("anchored=yes", out)


class TestAsyncVariants(unittest.TestCase):
    def setUp(self):
        self.fake = _FakeClient()
        client_mod._client = self.fake

    def tearDown(self):
        client_mod._client = self.fake

    def test_async_notarize(self):
        out = asyncio.run(aotrust_notarize_free_async("hello world"))
        self.assertIn("shield_id=9f2c1a", out)

    def test_async_verify(self):
        out = asyncio.run(aotrust_verify_async("job-123"))
        self.assertIn("valid=True", out)

    def test_async_status(self):
        out = asyncio.run(aotrust_status_async("job-123"))
        self.assertIn("status=anchored", out)


class TestBaseUrlNoV1(unittest.TestCase):
    """Двойной /v1 — ловится здесь: singleton обязан строиться БЕЗ /v1 суффикса."""

    def test_default_client_base_url_has_no_v1(self):
        from langchain_aotrust import get_client
        c = get_client()
        self.assertFalse(c.base_url.rstrip("/").endswith("/v1"),
                         f"base_url must NOT contain /v1 (got {c.base_url})")
        self.assertTrue(c.base_url.startswith("https://api.aotrust.link"))

    def test_configure_respects_custom_url(self):
        from langchain_aotrust import configure, get_client, reset_client
        configure(base_url="https://test.example.org")
        c = get_client()
        self.assertEqual(c.base_url, "https://test.example.org")
        reset_client()


if __name__ == "__main__":
    unittest.main()