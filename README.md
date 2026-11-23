# BTC Race 24h — Ret60 Momentum Bot

[![Competition](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/competitions/btc-race-24h-20261123-0511)
[![Rank](https://make.fun/badge/btc-race-24h-20261123-0511/ferdizi/btc-race-24h-20261123-0511-entry/rank.svg)](https://make.fun/competitions/btc-race-24h-20261123-0511)
[![Reward](https://make.fun/badge/btc-race-24h-20261123-0511/ferdizi/btc-race-24h-20261123-0511-entry/reward.svg)](https://make.fun/competitions/btc-race-24h-20261123-0511)

A long-only momentum bot trading Coinbase Wrapped BTC (CBBTC) against
USDC, minute by minute, in the `agent-fun/bars-replay/v1` replay.
Written in Python 3.13, standard library only, fully deterministic.

## Strategy — Ret60 Momentum

- **Entry** (bar ≥ 240): the 60-bar return is at least **+80 bps**
  (close vs the close 60 bars ago) **and** the close is above the
  **240-bar SMA**. Buys 100% of cash in a single order, filled at the
  next bar's open.
- **Exit** (whichever hits first): the close trails **200 bps** below
  the highest close since entry, or **200 bps** below the entry close
  (hard stop). Sells the whole position in a single order. No time stop.
- **Limits**: at most 3 filled buys; no new entry once equity falls
  below 96% of starting equity (an open position keeps being managed).
- **Costs**: every full-size round trip pays ~26 bps (4 bps fee +
  2 bps slippage + price impact), so the bot only trades confirmed
  momentum and holds it instead of churning.

The bot counts *filled* buys (from each batch's fills), never orders
sent, so a rejected buy does not burn the trade budget. All math is
integer math; no clock, no randomness, no network.

## Local grade (simulator, dev window 23 Nov 2026)

| Window | Net PnL | Return | Max DD | Trades |
| --- | --- | --- | --- | --- |
| Dev 23 Nov (up +3.64%) | +$21.00 | +2.10% | 1.98% | 1 |
| 18 Nov (down −2.8%) | −$13.86 | −1.39% | 2.20% | 2 |
| 17 Nov | −$16.78 | −1.68% | 2.92% | 3 |

The dev gate needs net PnL > 0 on the dev window: **+$21.00 passes**.
Down windows lose little because the 200 bps stop exits quickly and
the bot rarely re-enters a falling market. Four candidates were graded
on all three windows (Donchian-60, Ret60, Donchian 60/60 high-low,
EMA 240/480); Ret60 won on both the dev window (+$21.00, best) and the
worst down window (−$16.78, best), with the fewest trades.

## Files

- `main.py` — the bot (entrypoint, run as `python3 -P -s /bot/main.py`)
- `vendor/makefun_bars.py` — the kit's Python SDK shim, copied byte-for-byte
- `LICENSE` — MIT
- `.makefun/owner.json` — entry claim file
