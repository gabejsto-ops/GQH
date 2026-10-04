"""Daily portfolio simulation: monthly signals, next-open fills, drifting positions, costs on trades."""
import numpy as np
import pandas as pd


def simulate(opens: pd.DataFrame, closes: pd.DataFrame, weights: pd.DataFrame,
             cost_bps: float, exec_lag: int = 1, detail: bool = False,
             rf: pd.Series | None = None):
    """Run the strategy.

    weights: target weights indexed by signal date (a close). Each is executed at the open
    `exec_lag` trading days later (1 = next day). Between rebalances, dollar positions move with prices.

    Returns a daily frame with columns net, gross (returns) and turnover (traded notional / equity).
    With rf (daily risk-free return per date), also `excess`: the net return minus the cash return on the
    net exposure held during the day (the new book on rebalance days), i.e. sum_i w_i (r_i - rf). This is the return of a funded portfolio
    over cash, the convention in the TSMOM literature.
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
    rf_arr = None if rf is None else rf.reindex(dates).values
    rows, pnl_rows, traded_rows, pos_rows, exposure = [], [], [], [], []
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
        exposure.append(pos.sum() / start)               # book held through today (new book if rebalanced)
        pos, equity, day_pnl = pos + move, equity + move.sum(), day_pnl + move
        rows.append((equity / start - 1, (equity + paid) / start - 1, day_traded.sum() / start))
        if detail:
            pnl_rows.append(day_pnl / start)
            traded_rows.append(day_traded / start)
            pos_rows.append(pos / equity)

    idx = dates[first:]
    daily = pd.DataFrame(rows, index=idx, columns=["net", "gross", "turnover"])
    if rf_arr is not None:
        daily["excess"] = daily["net"] - np.array(exposure) * rf_arr[first:]
    if not detail:
        return daily
    as_frame = lambda rows_: pd.DataFrame(rows_, index=idx, columns=closes.columns)
    return daily, {"pnl": as_frame(pnl_rows), "traded": as_frame(traded_rows),
                   "positions": as_frame(pos_rows)}


def forward_returns(opens: pd.DataFrame, signal_dates: pd.DatetimeIndex,
                    rf: pd.Series | None = None) -> pd.DataFrame:
    """Open-to-open return from each signal's execution day to the next one. Last row is NaN.

    With rf, returns are in excess of the cash return over (approximately) the same month.
    """
    p = opens.index.get_indexer(signal_dates) + 1
    valid = p < len(opens.index)
    exec_open = pd.DataFrame(np.nan, index=signal_dates, columns=opens.columns)
    exec_open.loc[valid] = opens.values[p[valid]]
    fwd = exec_open.shift(-1) / exec_open - 1
    if rf is not None:
        growth = (1 + rf).cumprod().loc[signal_dates]
        fwd = fwd.sub(growth.shift(-1) / growth - 1, axis=0)
    return fwd
