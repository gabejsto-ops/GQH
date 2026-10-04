"""Daily portfolio simulation: monthly signals, next-open fills, drifting positions, costs on trades."""
import numpy as np
import pandas as pd


def simulate(opens: pd.DataFrame, closes: pd.DataFrame, weights: pd.DataFrame,
             cost_bps: float, exec_lag: int = 1, detail: bool = False):
    """Run the strategy.

    weights: target weights indexed by signal date (a close). Each is executed at the open
    `exec_lag` trading days later (1 = next day). Between rebalances, dollar positions move with prices.

    Returns a daily frame with columns net, gross (returns) and turnover (traded notional / equity).
    With detail=True, also returns per-asset frames: pnl, traded and positions, each as a fraction
    of the day's starting equity.
    """
    dates = closes.index
    O, C = opens.values, closes.values
    cost = cost_bps / 1e4

    execs = {}
    for p, row in zip(dates.get_indexer(weights.index), weights.values):
        if p < 0:
            raise ValueError("signal date not in price index")
        if p + exec_lag < len(dates):
            execs[p + exec_lag] = row
    first = min(execs)

    equity = 1.0
    pos = np.zeros(C.shape[1])  # dollar positions
    rows, pnl_rows, traded_rows, pos_rows = [], [], [], []
    for t in range(first, len(dates)):
        start, paid = equity, 0.0
        day_pnl, day_traded = np.zeros_like(pos), np.zeros_like(pos)
        if t in execs:
            move = pos * (O[t] / C[t - 1] - 1)           # overnight on old book
            pos, equity, day_pnl = pos + move, equity + move.sum(), day_pnl + move
            target = execs[t] * equity
            day_traded = np.abs(target - pos)
            paid = cost * day_traded.sum()
            pos, equity = target, equity - paid
            move = pos * (C[t] / O[t] - 1)               # open to close on new book
        else:
            move = pos * (C[t] / C[t - 1] - 1)
        pos, equity, day_pnl = pos + move, equity + move.sum(), day_pnl + move
        rows.append((equity / start - 1, (equity + paid) / start - 1, day_traded.sum() / start))
        if detail:
            pnl_rows.append(day_pnl / start)
            traded_rows.append(day_traded / start)
            pos_rows.append(pos / equity)

    idx = dates[first:]
    daily = pd.DataFrame(rows, index=idx, columns=["net", "gross", "turnover"])
    if not detail:
        return daily
    as_frame = lambda rows_: pd.DataFrame(rows_, index=idx, columns=closes.columns)
    return daily, {"pnl": as_frame(pnl_rows), "traded": as_frame(traded_rows),
                   "positions": as_frame(pos_rows)}


def forward_returns(opens: pd.DataFrame, signal_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Open-to-open return from each signal's execution day to the next one. Last row is NaN."""
    p = opens.index.get_indexer(signal_dates) + 1
    valid = p < len(opens.index)
    exec_open = pd.DataFrame(np.nan, index=signal_dates, columns=opens.columns)
    exec_open.loc[valid] = opens.values[p[valid]]
    return exec_open.shift(-1) / exec_open - 1
