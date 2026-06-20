"""Multi-signal market regime — deeper CMC usage ("Best Use of Agent Hub").

Blends THREE CMC data streams into one explainable risk-appetite score:
  - sentiment  (Fear & Greed)              — CONTRARIAN: extreme fear = opportunity
  - momentum   (core asset 7d % change)    — TREND: don't catch a falling knife
  - macro      (total market-cap 24h % + BTC dominance change) — regime backdrop

The blend is deliberate: a naive "buy fear" bot buys into crashes; gating the
contrarian sentiment with trend + macro means extreme fear during a hard
downtrend nets to ~neutral (hold) instead of a knife-catch.

Funding rates / derivatives positioning are NOT on our CMC tier (403/unavailable),
so they are intentionally absent rather than faked. They would slot in as
additional factors on a higher tier.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Signals:
    """The multi-stream snapshot the regime is scored from."""
    fear_greed: float           # 0-100
    momentum_7d_pct: float      # core asset 7d % change
    momentum_24h_pct: float     # core asset 24h % change
    macro_mcap_24h_pct: float   # total market cap 24h % change
    btc_dom_24h_change: float   # BTC dominance 24h percentage-point change
    classification: str = ""    # F&G label, for logging


@dataclass(frozen=True)
class RegimeWeights:
    # Trend-aware default. A backtest over 2025-26 ETH (see agent/backtest.py)
    # showed a contrarian-heavy mix (sentiment .40) catches falling knives and
    # underperforms buy-hold; shifting weight to momentum (trend-following)
    # monotonically cut drawdown. These weights are tuned on ONE downtrend year
    # — directionally sound (trend-following reduces drawdown) but NOT proven
    # optimal; expect whipsaw in ranging markets.
    sentiment: float = 0.20
    momentum: float = 0.50
    macro: float = 0.20
    dominance: float = 0.10


@dataclass(frozen=True)
class RegimeScore:
    score: float                # [-1, 1]
    label: str                  # 'risk-on' | 'neutral' | 'risk-off'
    breakdown: dict = field(default_factory=dict)

    def log_line(self) -> str:
        parts = " ".join(f"{k}={v:+.3f}" for k, v in self.breakdown.items())
        return f"{self.label} score={self.score:+.3f} [{parts}]"


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def score(s: Signals, w: RegimeWeights | None = None, threshold: float = 0.20) -> RegimeScore:
    """Weighted multi-factor regime score in [-1, 1], with a per-factor breakdown."""
    w = w or RegimeWeights()
    # Normalize each raw signal into a [-1, 1] contribution.
    sentiment = _clamp((50.0 - s.fear_greed) / 50.0)     # fear -> positive (buy)
    momentum = _clamp(s.momentum_7d_pct / 15.0)          # +15% / 7d -> +1
    macro = _clamp(s.macro_mcap_24h_pct / 5.0)           # +5% mcap/24h -> +1
    dominance = _clamp(-s.btc_dom_24h_change / 2.0)       # rising BTC dom -> alt risk-off

    breakdown = {
        "sentiment": round(w.sentiment * sentiment, 4),
        "momentum": round(w.momentum * momentum, 4),
        "macro": round(w.macro * macro, 4),
        "dominance": round(w.dominance * dominance, 4),
    }
    total = round(sum(breakdown.values()), 4)
    label = "risk-on" if total >= threshold else "risk-off" if total <= -threshold else "neutral"
    return RegimeScore(score=total, label=label, breakdown=breakdown)
