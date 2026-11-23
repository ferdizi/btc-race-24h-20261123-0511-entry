"""Ret60 Momentum — BTC race bot (agent-fun/bars-replay/v1).

Long-only momentum follower on CBBTC, minute bars, $1,000 start.
Entry: bar >= 240, 60-bar return (close vs close 60 bars ago) is at
least +80 bps, and close is above the 240-bar SMA. Buys 100% of cash
in one order at the next bar's open.
Exit (whichever hits first): close trails 200 bps below the highest
close since entry, or 200 bps below the entry close (hard stop).
No time stop. Sells the whole position in one order.
At most 3 filled buys total; no new entry once equity falls below 96%
of starting equity (an open position keeps being managed).
Deterministic: integer math only, no clock, no randomness, no network.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
SLIPPAGE_BPS = 300
LOOKBACK = 60
RET60_BPS = 80
SMA_LEN = 240
MIN_BAR = 240
TRAIL_BPS = 200
STOP_BPS = 200
MAX_TRADES = 3
HALT_EQUITY_BPS = 9600  # 96% of starting equity

closes = []
entry_close = None
entry_high = None
entry_idx = None
buys_filled = 0
start_equity = None


def on_batch(state, batch):
    global entry_close, entry_high, entry_idx, buys_filled, start_equity

    if start_equity is None:
        start_equity = int(state.hello["capital"]["quote_units"])

    # Count filled buys from this batch's fills: the trade cap counts
    # trades that actually filled, not orders sent (a rejected buy must
    # not burn the budget). Fills of the previous bar's orders are
    # already applied to state before this callback runs, so a position
    # seen here is real and a missing one means the order was rejected.
    for fill in batch.get("fills", []):
        if fill.get("side") == "buy" and fill.get("status") == "filled":
            buys_filled += 1

    close = state.close(SYMBOL)
    if close is None:
        return []
    closes.append(close)
    n = len(closes)

    holding = state.positions.get(SYMBOL)
    if holding is not None and holding.qty > 0:
        # Manage the open position: track the running high, check exits.
        # No latch: if a sell is rejected, the position is still here
        # next bar and the exit condition simply fires again.
        if entry_high is None or entry_close is None:
            entry_close = close
            entry_high = close
            entry_idx = n - 1
        elif close > entry_high:
            entry_high = close
        trail_line = entry_high * (10000 - TRAIL_BPS) // 10000
        stop_line = entry_close * (10000 - STOP_BPS) // 10000 if entry_close else 0
        if close < trail_line or close < stop_line:
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": SLIPPAGE_BPS}]
        return []

    # Flat: a sell just filled (or never held) — clear entry state.
    entry_close = None
    entry_high = None
    entry_idx = None

    if state.warming_up:
        return []
    if buys_filled >= MAX_TRADES:
        return []
    if state.equity < start_equity * HALT_EQUITY_BPS // 10000:
        return []
    if n < MIN_BAR + 1:
        return []
    if state.cash <= 0:
        return []

    # 60-bar return vs the close 60 bars ago (excludes the current
    # bar from the reference point); SMA240 includes the current bar.
    if len(closes) < LOOKBACK + 1:
        return []
    ret60_line = closes[-LOOKBACK - 1] * (10000 + RET60_BPS) // 10000
    sma240 = sum(closes[-SMA_LEN:]) // SMA_LEN
    if close >= ret60_line and close > sma240:
        entry_close = close
        entry_high = close
        entry_idx = n - 1
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
