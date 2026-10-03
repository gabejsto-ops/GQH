"""Daily portfolio simulation: monthly signals, next-open fills, drifting positions, costs on trades."""
import numpy as np
import pandas as pd


def simulate(opens: pd.DataFrame, closes: pd.DataFrame, weights: pd.DataFrame,
             cost_bps: float) -> pd.DataFrame:
    """Run the strategy.

    weights: target weights indexed by signal date (a close). Each is executed at the open of the
    next trading day. Between rebalances, dollar positions move with prices.

    Returns a daily frame with columns net, gross (returns) and turnover (traded notional / equity).
    """
    dates = closes.index
    O, C = opens.values, closes.values
    cost = cost_bps / 1e4

    execs = {}
    for p, row in zip(dates.get_indexer(weights.index), weights.values):
        if p < 0:
            raise ValueError("signal date not in price index")
        if p + 1 < len(dates):
            execs[p + 1] = row
    first = min(execs)

    equity = 1.0
    pos = np.zeros(C.shape[1])  # dollar positions
    rows = []
    for t in range(first, len(dates)):
        start, traded, paid = equity, 0.0, 0.0
        if t in execs:
            move = pos * (O[t] / C[t - 1] - 1)           # overnight on old book
            pos, equity = pos + move, equity + move.sum()
            target = execs[t] * equity
            traded = np.abs(target - pos).sum()
            paid = cost * traded
            pos, equity = target, equity - paid
            move = pos * (C[t] / O[t] - 1)               # open to close on new book
        else:
            move = pos * (C[t] / C[t - 1] - 1)
        pos, equity = pos + move, equity + move.sum()
        rows.append((equity / start - 1, (equity + paid) / start - 1, traded / start))

    return pd.DataFrame(rows, index=dates[first:], columns=["net", "gross", "turnover"])


def forward_returns(opens: pd.DataFrame, signal_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Open-to-open return from each signal's execution day to the next one. Last row is NaN."""
    p = opens.index.get_indexer(signal_dates) + 1
    valid = p < len(opens.index)
    exec_open = pd.DataFrame(np.nan, index=signal_dates, columns=opens.columns)
    exec_open.loc[valid] = opens.values[p[valid]]
    return exec_open.shift(-1) / exec_open - 1
