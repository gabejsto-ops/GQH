"""Signals and state variables. Every function uses data up to and including each row's date only."""
import numpy as np
import pandas as pd
from scipy.stats import norm

from src.config import (ER_THRESHOLD, ER_WINDOW, MAX_ABS_WEIGHT, STATE_PCTL, STATE_VOL,
                        TARGET_VOL, VOL_LONG, VOL_SHORT)


def month_end_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each calendar month present in the index."""
    s = pd.Series(index, index=index)
    return pd.DatetimeIndex(s.groupby([index.year, index.month]).last().values)


def trailing_return(closes: pd.DataFrame, lookback: int) -> pd.DataFrame:
    return closes / closes.shift(lookback) - 1


def trend_z(closes: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """t-stat of the mean daily return over the lookback: mean / std * sqrt(L)."""
    r = closes.pct_change()
    return r.rolling(lookback).mean() / r.rolling(lookback).std() * np.sqrt(lookback)


def realized_vol(closes: pd.DataFrame, window: int) -> pd.DataFrame:
    """Annualized standard deviation of daily close-to-close returns."""
    return closes.pct_change().rolling(window).std() * np.sqrt(252)


def high_vol_state(closes: pd.DataFrame) -> pd.DataFrame:
    """True when 21-day vol is above its own trailing-252-day 75th percentile. NaN during warm-up."""
    v = realized_vol(closes, STATE_VOL)
    threshold = v.rolling(252).quantile(STATE_PCTL)
    return (v > threshold).where(threshold.notna())


def efficiency_ratio(closes: pd.DataFrame, window: int = ER_WINDOW) -> pd.DataFrame:
    """|net move| / total path length over the window (Kaufman). 1 = straight line, ~0.22 = noise."""
    net = (closes - closes.shift(window)).abs()
    path = closes.diff().abs().rolling(window).sum()
    return net / path


def features(closes: pd.DataFrame) -> dict[str, pd.DataFrame]:
    hv = high_vol_state(closes)
    er = efficiency_ratio(closes)
    return {
        "vol_short": realized_vol(closes, VOL_SHORT),
        "vol_long": realized_vol(closes, VOL_LONG),
        "high_vol": hv,
        "er": er,
        "shock": (hv == 1) & (er > ER_THRESHOLD),
    }


def target_weights(closes: pd.DataFrame, feats: dict, lookback: int, sizing: str,
                   dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Target weights (fraction of equity) on each signal date."""
    n = closes.shape[1]
    sign = np.sign(trailing_return(closes, lookback)).loc[dates]
    if sizing == "S0":
        w = sign / n
    elif sizing in ("S1", "S2", "S3", "S4"):
        vol = feats["vol_short"].loc[dates]
        if sizing == "S2":
            # On information shocks, size with long-run vol: do not de-risk.
            vol = vol.where(~feats["shock"].loc[dates], feats["vol_long"].loc[dates])
        w = sign * (TARGET_VOL / n) / vol
        if sizing == "S3":
            # Bayesian confidence: posterior P(drift > 0) under a flat prior, mapped to [-1, 1].
            # (2*Phi(z) - 1) already carries the sign of z, so drop the separate sign.
            w = w.abs() * (2 * norm.cdf(trend_z(closes, lookback).loc[dates]) - 1)
        if sizing == "S4":
            # Calm, efficient trends: double the bet.
            calm_efficient = (feats["high_vol"].loc[dates] == 0) & (feats["er"].loc[dates] > ER_THRESHOLD)
            w = w.where(~calm_efficient, 2 * w)
    else:
        raise ValueError(sizing)
    return w.clip(-MAX_ABS_WEIGHT, MAX_ABS_WEIGHT)


def common_signal_dates(closes: pd.DataFrame, feats: dict, max_lookback: int) -> pd.DatetimeIndex:
    """Month-ends where every input for every variant exists for all assets."""
    ready = (trailing_return(closes, max_lookback).notna()
             & feats["vol_long"].notna()
             & feats["high_vol"].notna()
             & feats["er"].notna()).all(axis=1)
    dates = month_end_dates(closes.index)
    return dates[ready.loc[dates].values]
