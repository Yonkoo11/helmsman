"""Backtest the regime strategy against history — validate, don't just reason.

Replays the SAME `agent.regime.score` engine the live agent uses over ~1y of
daily data, and compares the risk-governed strategy to buy-and-hold ETH. The
product thesis is "most profit WITHOUT blowing up", so the metric that matters
most is **max drawdown** — the strategy should de-risk in risk-off regimes and
draw down less than buy-and-hold.

Data: ETH daily price (CoinGecko, free) + Fear&Greed history (CMC). Momentum is
derived from price. Macro + dominance are held neutral here (no faithful daily
history on our tier), so this validates the sentiment+momentum core — disclosed,
not hidden.

  PYTHONPATH=. .venv/bin/python -m agent.backtest [--days 365]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess

import requests

from . import data_cmc  # noqa: F401 — import triggers .env load (CMC_API_KEY)
from .regime import RegimeWeights, Signals, score


def _day(ts_seconds: float) -> str:
    return _dt.datetime.fromtimestamp(ts_seconds, _dt.timezone.utc).strftime("%Y-%m-%d")


def fetch_eth_prices(days: int) -> dict[str, float]:
    # CoinGecko's WAF rejects requests' TLS fingerprint; curl works in this env.
    url = ("https://api.coingecko.com/api/v3/coins/ethereum/market_chart"
           f"?vs_currency=usd&days={days}&interval=daily")
    proc = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=40)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(f"CoinGecko fetch failed: {proc.stderr[:200]}")
    data = json.loads(proc.stdout)
    out: dict[str, float] = {}
    for ts_ms, price in data["prices"]:
        out[_day(ts_ms / 1000.0)] = float(price)
    return out


def fetch_fg_history(limit: int) -> dict[str, float]:
    key = os.getenv("CMC_API_KEY")
    r = requests.get(
        "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical",
        headers={"X-CMC_PRO_API_KEY": key}, params={"limit": str(limit)}, timeout=30,
    )
    r.raise_for_status()
    return {_day(float(d["timestamp"])): float(d["value"]) for d in r.json()["data"]}


def _max_drawdown(curve: list[float]) -> float:
    peak, mdd = curve[0], 0.0
    for v in curve:
        peak = max(peak, v)
        mdd = max(mdd, (peak - v) / peak)
    return mdd * 100.0


def run(days: int = 365, per_trade_step: float = 0.10, fee: float = 0.001,
        weights: RegimeWeights | None = None) -> dict:
    prices = fetch_eth_prices(days)
    fg = fetch_fg_history(min(days + 10, 500))
    dates = sorted(set(prices) & set(fg))
    if len(dates) < 30:
        raise RuntimeError(f"only {len(dates)} aligned days — not enough to backtest")

    px = [prices[d] for d in dates]
    weight = 0.0          # strategy ETH weight; start flat (in stable)
    equity = 1.0          # strategy equity (normalized)
    bh = 1.0              # buy-and-hold ETH equity
    eq_curve, bh_curve = [1.0], [1.0]
    trades, label_counts = 0, {"risk-on": 0, "neutral": 0, "risk-off": 0}

    for i in range(7, len(dates)):
        eth_ret = px[i] / px[i - 1] - 1.0
        equity *= (1 + weight * eth_ret)   # held old weight through the day
        bh *= (1 + eth_ret)
        eq_curve.append(equity)
        bh_curve.append(bh)

        mom7d = (px[i] / px[i - 7] - 1.0) * 100.0
        rs = score(Signals(fg[dates[i]], mom7d, 0.0, 0.0, 0.0), weights)
        label_counts[rs.label] += 1
        target = 1.0 if rs.label == "risk-on" else 0.0 if rs.label == "risk-off" else weight

        step = min(abs(target - weight), per_trade_step)
        if step > 1e-9:
            equity *= (1 - fee * step)     # fee on the traded fraction
            weight += step if target > weight else -step
            trades += 1

    return {
        "period": f"{dates[7]} .. {dates[-1]}",
        "days": len(dates) - 7,
        "strategy_return_pct": round((equity - 1) * 100, 2),
        "strategy_max_drawdown_pct": round(_max_drawdown(eq_curve), 2),
        "buyhold_return_pct": round((bh - 1) * 100, 2),
        "buyhold_max_drawdown_pct": round(_max_drawdown(bh_curve), 2),
        "trades": trades,
        "regime_days": label_counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    res = run(days=ap.parse_args().days)
    print("Helmsman regime backtest (sentiment+momentum core; macro/dominance neutral)")
    for k, v in res.items():
        print(f"  {k:28} {v}")
    s_ret, b_ret = res["strategy_return_pct"], res["buyhold_return_pct"]
    s_dd, b_dd = res["strategy_max_drawdown_pct"], res["buyhold_max_drawdown_pct"]
    print(f"\n  thesis check — drawdown: strategy {s_dd}% vs buy-hold {b_dd}% "
          f"({'LOWER (de-risked) ✓' if s_dd < b_dd else 'NOT lower ✗'})")
    print(f"  return: strategy {s_ret}% vs buy-hold {b_ret}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
