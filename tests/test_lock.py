"""Tests for the single-instance lock (review #7)."""
from __future__ import annotations

import pytest

from agent.lock import AlreadyRunning, single_instance


def test_second_concurrent_instance_is_blocked(tmp_path):
    p = tmp_path / "agent.lock"
    with single_instance(p):
        with pytest.raises(AlreadyRunning):
            with single_instance(p):
                pass  # pragma: no cover


def test_lock_is_released_after_exit(tmp_path):
    p = tmp_path / "agent.lock"
    with single_instance(p):
        pass
    # Re-acquiring after release must succeed.
    with single_instance(p):
        pass
