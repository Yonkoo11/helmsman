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
import time

import requests

from . import data_cmc  # noqa: F401 — import triggers .env load (CMC_API_KEY)
from .regime import RegimeWeights, Signals, score


def _day(ts_seconds: float) -> str:
    return _dt.datetime.fromtimestamp(ts_seconds, _dt.timezone.utc).strftime("%Y-%m-%d")


def fetch_prices(coin_id: str, days: int) -> dict[str, float]:
    # CoinGecko's WAF rejects requests' TLS fingerprint; curl works in this env.
    # Free tier rate-limits bursts, so retry with backoff.
    url = (f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
           f"?vs_currency=usd&days={days}&interval=daily")
    last = ""
    for attempt in range(4):
        proc = subprocess.run(["curl", "-s", url], capture_output=True, text=True, timeout=40)
        out = proc.stdout.strip()
        if out:
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                last = out[:160]
            else:
                if "prices" in data and data["prices"]:
                    return {_day(t / 1000.0): float(p) for t, p in data["prices"]}
                last = str(data)[:160]
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"CoinGecko fetch failed for {coin_id}: {last}")


def fetch_eth_prices(days: int) -> dict[str, float]:
    return fetch_prices("ethereum", days)


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


def _simulate(dates: list[str], px: list[float], fg: dict[str, float],
              macro: dict[str, float], dom: dict[str, float],
              weights: RegimeWeights | None, per_trade_step: float = 0.10,
              fee: float = 0.001) -> tuple[list[float], list[float], int]:
    weight, equity, bh = 0.0, 1.0, 1.0
    eq_curve, bh_curve, trades = [1.0], [1.0], 0
    for i in range(7, len(dates)):
        ret = px[i] / px[i - 1] - 1.0
        equity *= (1 + weight * ret)
        bh *= (1 + ret)
        eq_curve.append(equity)
        bh_curve.append(bh)
        mom7d = (px[i] / px[i - 7] - 1.0) * 100.0
        d = dates[i]
        rs = score(Signals(fg.get(d, 50.0), mom7d, 0.0, macro.get(d, 0.0), dom.get(d, 0.0)), weights)
        target = 1.0 if rs.label == "risk-on" else 0.0 if rs.label == "risk-off" else weight
        step = min(abs(target - weight), per_trade_step)
        if step > 1e-9:
            equity *= (1 - fee * step)
            weight += step if target > weight else -step
            trades += 1
    return eq_curve, bh_curve, trades


def _metrics(eq: list[float], bh: list[float]) -> dict:
    return {"ret": round((eq[-1] - 1) * 100, 1), "dd": round(_max_drawdown(eq), 1),
            "bh_ret": round((bh[-1] - 1) * 100, 1), "bh_dd": round(_max_drawdown(bh), 1)}


def robustness(days: int = 365, weights: RegimeWeights | None = None) -> list:
    """Multi-asset + walk-forward + all-4-factor stress test of the tuned weights."""
    fg = fetch_fg_history(min(days + 10, 500))
    assets = {"BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin"}
    prices = {sym: fetch_prices(cid, days) for sym, cid in assets.items()}
    common = sorted(set.intersection(*[set(p) for p in prices.values()]) & set(fg))
    if len(common) < 40:
        raise RuntimeError(f"only {len(common)} common dates")

    # Market proxy so macro + dominance factors are ACTIVE (not held neutral):
    # macro = equal-weight basket 24h return; dominance = BTC price-share change.
    base = {sym: prices[sym][common[0]] for sym in assets}
    idx = {d: sum(prices[s][d] / base[s] for s in assets) / len(assets) for d in common}
    share = {d: prices["BTC"][d] / sum(prices[s][d] for s in assets) for d in common}
    macro, dom = {}, {}
    for i, d in enumerate(common):
        p = common[i - 1] if i else d
        macro[d] = 0.0 if i == 0 else (idx[d] / idx[p] - 1) * 100
        dom[d] = 0.0 if i == 0 else (share[d] - share[p]) * 100

    rows = []
    mid = len(common) // 2
    windows = [("full", 0, len(common)), ("H1", 0, mid), ("H2", mid, len(common))]
    for sym in assets:
        for tag, a, b in windows:
            dsl, psl = common[a:b], [prices[sym][d] for d in common[a:b]]
            if len(dsl) > 10:
                eq, bh, tr = _simulate(dsl, psl, fg, macro, dom, weights)
                rows.append((sym, tag, _metrics(eq, bh), tr))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--robustness", action="store_true",
                    help="multi-asset + walk-forward + all-4-factor stress test")
    args = ap.parse_args()
    if args.robustness:
        rows = robustness(days=args.days)
        print("Robustness (tuned weights, all 4 factors via market proxy)")
        print(f"  {'asset/window':16} {'strat ret%':>10} {'strat DD%':>10} "
              f"{'bh ret%':>9} {'bh DD%':>8}  verdict")
        wins = 0
        for sym, tag, m, tr in rows:
            better = m["dd"] < m["bh_dd"] and m["ret"] >= m["bh_ret"]
            wins += better and tag == "full"
            mark = "DD↓&ret≥" if better else ("DD↓" if m["dd"] < m["bh_dd"] else "—")
            print(f"  {sym+'/'+tag:16} {m['ret']:>10} {m['dd']:>10} "
                  f"{m['bh_ret']:>9} {m['bh_dd']:>8}  {mark}")
        print(f"\n  beats buy-hold on BOTH (full window): {wins}/3 assets")
        return 0
    res = run(days=args.days)
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
