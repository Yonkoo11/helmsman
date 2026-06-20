"""Single-instance lock (review #7) — never let two runs trade at once.

An unattended scheduler can fire an overlapping run before the previous one
finishes; without a lock the agent would double-trade and corrupt turnover/peak
state. This advisory file lock makes a second concurrent run exit immediately.
"""
from __future__ import annotations

import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

DEFAULT_LOCK = Path(__file__).resolve().parent.parent / "runtime" / "agent.lock"


class AlreadyRunning(RuntimeError):
    pass


@contextmanager
def single_instance(path: Path = DEFAULT_LOCK):
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "w")
    try:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as e:
            raise AlreadyRunning(f"another agent instance holds {path}") from e
        f.write(str(os.getpid()))
        f.flush()
        yield
    finally:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        finally:
            f.close()
