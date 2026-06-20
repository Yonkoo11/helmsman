"""Durable risk state — what makes the safety caps actually work across runs.

The drawdown circuit breaker and the daily turnover cap are only meaningful if
peak equity and same-day turnover survive between invocations. This module owns
that persistence. Without it, the breaker can never fire (peak == current every
run) and the daily cap always reads zero — the two critical review findings.

The UTC day is injected so the rollover logic is testable without a clock.
"""
from __future__ import annotations

import datetime as _dt
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "runtime" / "state.json"


def today_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


@dataclass
class RiskState:
    peak_equity_usd: float = 0.0
    day_utc: str = ""
    traded_today_usd: float = 0.0
    last_trade_day_utc: str = ""
    trades_total: int = 0

    # --- transitions (all pure given an injected `day`) ---

    def roll_day(self, day: str) -> None:
        """Reset same-day counters when the UTC day changes."""
        if self.day_utc != day:
            self.day_utc = day
            self.traded_today_usd = 0.0

    def observe_equity(self, equity_usd: float) -> None:
        """Track the high-water mark the drawdown breaker measures against."""
        if equity_usd > self.peak_equity_usd:
            self.peak_equity_usd = equity_usd

    def record_trade(self, notional_usd: float, day: str) -> None:
        self.roll_day(day)
        self.traded_today_usd += notional_usd
        self.last_trade_day_utc = day
        self.trades_total += 1

    def traded_today(self, day: str) -> float:
        """Same-day turnover, accounting for an un-saved day rollover."""
        return 0.0 if self.day_utc != day else self.traded_today_usd

    def has_traded_on(self, day: str) -> bool:
        return self.last_trade_day_utc == day


def load(path: Path = DEFAULT_PATH) -> RiskState:
    if not path.exists():
        return RiskState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        known = {f: data[f] for f in RiskState().__dict__ if f in data}
        return RiskState(**known)
    except (json.JSONDecodeError, OSError, TypeError):
        return RiskState()  # never let a corrupt state file halt the agent


def save(state: RiskState, path: Path = DEFAULT_PATH) -> None:
    """Atomic write so a crash mid-save can't corrupt the state file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2)
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
