# Helmsman: Regime Backtest (2026-06-20)

Replays the **same `agent.regime.score` engine the live agent uses** over ~357
days of daily data (2025-06-28 .. 2026-06-19): ETH price (CoinGecko) + Fear&Greed
history (CMC). Momentum derived from price; macro + dominance held neutral (no
faithful daily history on our CMC tier), so this validates the sentiment+momentum
core, disclosed not hidden.

## Why we ran it
The strategy thesis is "most profit WITHOUT blowing up." Before trusting any
weights live, validate that the regime actually de-risks. The first run **failed
that test honestly** and forced a fix.

## Weight sweep (same data, sentiment vs momentum mix)
| Config | sentiment/momentum | return % | max DD % | risk-off days |
|--------|--------------------|----------|----------|---------------|
| A (original default) | .40 / .30 | **-53.8** | 61.2 | 1 |
| B | .30 / .40 | -28.2 | 57.1 | 19 |
| C (**adopted**) | .20 / .50 | **-15.1** | **49.3** | 63 |
| D | .10 / .60 | +0.8 | 39.6 | 88 |
| Buy-and-hold ETH | — | -29.2 | 67.5 | — |

Monotonic: shifting weight from contrarian-sentiment to trend-momentum improved
BOTH return and drawdown. The original default (A) was the worst, it kept buying
fear into a downtrend (1 risk-off day in a year) and lost ~2x buy-hold.

## Decision
Adopted **C (sentiment .20 / momentum .50)** as the default, NOT the single best
(D). Picking D would be curve-fitting to one downtrend year. C is a defensible
middle: trend-aware (theory-backed drawdown reduction) while keeping sentiment as
a secondary factor. With C the strategy beats buy-hold on both axes:
**-15.1% vs -29.2% return, 49.3% vs 67.5% drawdown.**

## Honest caveats
- Tuned on ONE year of ETH (a downtrend). Trend-following whipsaws in ranging
  markets, live results will differ, possibly worse.
- Only 2 of 4 regime factors backtested (macro/dominance neutral).
- Daily granularity; flat 0.1% fee, no slippage/MEV modeling.
- A 1-week live competition is variance-dominated; this validates the risk-control
  direction, not a profit guarantee.

Reproduce: `PYTHONPATH=. .venv/bin/python -m agent.backtest --days 365`

## Robustness, addressing the overfit risk (2026-06-20)
`PYTHONPATH=. .venv/bin/python -m agent.backtest --robustness`

Multi-asset + walk-forward + ALL 4 factors active (macro/dominance reconstructed
from an equal-weight BTC/ETH/BNB basket proxy + BTC price-share).

| asset/window | strat ret% | strat DD% | bh ret% | bh DD% |
|---|---|---|---|---|
| BTC/full | -40.3 | 42.8 | -41.2 | 51.2 |
| ETH/full | -7.9 | 43.9 | -29.2 | 67.5 |
| BNB/full | -5.0 | 43.6 | -10.0 | 56.4 |
| (H1/H2 halves) | — | DD lower in all 18 windows | — | — |

Findings:
- **3/3 assets beat buy-hold on BOTH return and drawdown** (full window), not ETH-specific.
- **Drawdown lower than buy-hold in EVERY one of the 18 asset×window cells**, the
  risk-control claim is robust across assets and sub-periods.
- Honest trade-off: in bullish first-halves the strategy's RETURN lags buy-hold
  (under-participates in rallies), the expected cost of trend-following / "don't blow up".
- All-4-factor (with macro/dominance proxy) beat the 2-factor core on ETH (-7.9 vs -15.1),
  evidence macro/dominance add signal.

Remaining honest limits: still ~1y window (F&G history cap); macro/dominance are a
price-basket PROXY, not the exact CMC series; rally under-participation is real.
