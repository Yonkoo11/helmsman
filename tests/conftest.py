"""Test safety net: no test may make a real twak/npx/curl subprocess call.

A test that forgets to mock the execution path could otherwise sign a REAL
on-chain trade (this happened once). This autouse guard blocks such calls loudly
so the failure is a clear error, never a real money movement. Tests that need
subprocess behaviour mock it themselves; this only catches the ones that forget.
"""
import subprocess

import pytest


@pytest.fixture(autouse=True)
def _block_real_external_calls(monkeypatch):
    real_run = subprocess.run

    def guarded(args, *a, **k):
        cmd = args if isinstance(args, str) else " ".join(str(x) for x in (args or []))
        if any(tok in cmd for tok in ("twak", "npx", "curl ", "/curl")):
            raise RuntimeError(f"TEST SAFETY: blocked real external call: {cmd[:80]}")
        return real_run(args, *a, **k)

    monkeypatch.setattr(subprocess, "run", guarded)
